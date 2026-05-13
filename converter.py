import pandas as pd
import re
import os

CODE_AFFAIRE_PATH = os.path.join(os.path.dirname(__file__), 'CODE_AFFAIRE.xlsx')

# ── Référentiel codes affaires rétro (Altios) ────────────────────────────────
def load_retro():
    df = pd.read_excel(CODE_AFFAIRE_PATH, sheet_name='Codes Affaires Retro', header=None)
    df = df.iloc[4:].reset_index(drop=True)
    df.columns = ['Type', 'Code', 'empty', 'Libelle', 'Honoraires', 'empty2', 'Frais']
    df = df[df['Code'] != 'Code Affaires Retro'].dropna(subset=['Code'])
    df = df.drop_duplicates(subset='Code')
    result = {}
    for _, row in df.iterrows():
        try:
            result[row['Code']] = {'honoraires': int(row['Honoraires']), 'frais': int(row['Frais'])}
        except:
            pass
    return result

# ── Référentiel codes affaires client ────────────────────────────────────────
def load_client():
    df = pd.read_excel(CODE_AFFAIRE_PATH, sheet_name='Codes affaires client', header=None)
    df = df.iloc[2:].reset_index(drop=True)
    df.columns = ['Type', 'Code', 'empty', 'Libelle', 'France', 'CEE', 'Export']
    df = df.dropna(subset=['Code'])
    result = {}
    for _, row in df.iterrows():
        code = str(row['Code']).strip()
        if not code or code == 'nan':
            continue
        def safe_int(v):
            try: return int(v)
            except: return None
        result[code] = {
            'france': safe_int(row['France']),
            'cee':    safe_int(row['CEE']),
            'export': safe_int(row['Export']),
        }
    return result

# ── Entités Altios ────────────────────────────────────────────────────────────
PARTNER_TO_CODE_UPPER = {
    'ALTIOS FRANCE SAS':                                        None,
    'ALTIOS SOUTH EAST ASIA PRIVATE LIMITED':                   'FSI',
    'ALTIOS CORPORATE SERVICES SAS':                            None,
    'ALTIOS INTERNATIONAL SAS':                                 None,
    'ALTIOS MALAYSIA SDN BHD':                                  'FSI',
    'ALTIOS VN LIMITED LIABILITY':                              'FSI',
    'MAIER + VIDORNO GMBH':                                     'FAL',
    'ALTIOS GERMANY GMBH':                                      'FAL',
    'ALTIOS POLSKA S.P.Z.O.O.':                                 'FPO',
    'ALTIOS ČESKÁ REPUBLIKA S.R.O.':                            None,
    'ALTIOS CONSULTING LIMITED':                                'FAN',
    'FRENGER BUSINESS SERVICES LIMITED':                        'FAN',
    'FRENGER CONSULTING SERVICES LIMITED':                      'FAN',
    'ALTIOS SPAIN SOCIEDAD LIMITADA':                           'FES',
    'LUSIALTIOS UNIPESSOAL LDA':                                'FPORT',
    'ALTIOS ITALIA SRL':                                        'FIT',
    'ALTIOS CHINA LIMITED':                                     'FCH',
    'ALTIOS ASIA LIMITED':                                      'FHK',
    'ALTIOS HONG-KONG LIMITED':                                 'FHK',
    'ALTIOS AUSTRALIA PTY LIMITED':                             'FAU',
    'ALTIOS NEW ZEALAND LIMITED':                               'FAU',
    'ALTIOS INTERNATIONAL INC':                                 'FUS',
    'ALTIOS CONSEILS INC':                                      'FCA',
    'ALTIOS ADVISORY MEXICO S.A DE C.V':                        'FME',
    'ALTIOS LATAM SERVICES S.A DE C.V':                         'FME',
    'DP2B INTERNATIONAL S.A DE C.V':                            'FME',
    'ALTIOS DO BRASIL CONSULTORIA E REPRESENTACOES LTDA':       'FBR',
    'ALTIOS INTERNATIONAL FZCO':                                'FEA',
    'ALTIOS CONSULTING PRIVATE LIMITED':                        'FIN',
    'M AND V MARKETING AND SALES PRIVATE LIMITED':              'FIN',
    'M AND V MARKETING DEVELOPMENT SERVICES PRIVATE LIMITED':   'FIN',
    'M&V MARKET DEVELOPMENT SERVICE PVT. LTD':                  'FIN',
    'SELECTCHEMIE SERVICES PRIVATE LIMITED':                    'FIN',
    'ALTIOS INTERNATIONAL UK LIMITED':                          'FAN',
}
ALTIOS_UPPER = set(PARTNER_TO_CODE_UPPER.keys())

def is_altios(partner):
    return str(partner).strip().upper() in ALTIOS_UPPER

def get_code_altios(partner):
    return PARTNER_TO_CODE_UPPER.get(str(partner).strip().upper()) or ''

# ── Helpers ───────────────────────────────────────────────────────────────────
def fmt_date(val):
    if pd.isna(val): return ''
    if hasattr(val, 'strftime'): return val.strftime('%d%m%y')
    return str(val)

def fmt_decimal(val):
    if val == '' or (isinstance(val, float) and pd.isna(val)):
        return '0,00'
    try:
        return f"{float(val):.2f}".replace('.', ',')
    except:
        return '0,00'

def compte_tiers(partner):
    if pd.isna(partner) or not str(partner).strip(): return ''
    p = re.sub(r'[^A-Za-z0-9]', '', partner.upper())[:14]
    return '411' + p

def compte_general(compte_odoo, code_analytique, taxe, altios, code_to_comptes, code_client):
    if pd.isna(compte_odoo): return ''
    num = re.match(r'^(\d+)', str(compte_odoo))
    if not num: return str(compte_odoo)
    n = num.group(1)

    if n.startswith('411'): return '41100000'
    if n.startswith('445'): return n

    if altios:
        if not code_analytique or code_analytique not in code_to_comptes:
            return n
        comptes = code_to_comptes[code_analytique]
        if n == '706100':   return str(comptes['honoraires'])
        elif n in ('706200', '706300'): return str(comptes['frais'])
        else: return n
    else:
        if n not in ('706000', '706010', '706200', '706300'): return n
        if not code_analytique or code_analytique not in code_client: return n
        comptes = code_client[code_analytique]
        taxe_str = str(taxe).upper() if pd.notna(taxe) else ''
        if 'EX' in taxe_str:   col = 'export'
        elif 'EU' in taxe_str: col = 'cee'
        elif '20%' in taxe_str: col = 'france'
        else: col = None
        compte = comptes.get(col) if col else None
        return str(compte) if compte else n

# ── Conversion principale ─────────────────────────────────────────────────────
def convert(odoo_file):
    code_to_comptes = load_retro()
    code_client     = load_client()

    df = pd.read_excel(odoo_file)

    lines = []
    for _, r in df.iterrows():
        partner   = r['Partenaire']
        altios    = is_altios(partner)

        if altios:
            code = get_code_altios(partner)
        else:
            ref  = str(r['Référence']).strip().split()[0] if pd.notna(r['Référence']) else ''
            code = ref if ref in code_client else ''

        cg   = compte_general(r['Compte'], code, r['Taxes'], altios, code_to_comptes, code_client)
        ct   = compte_tiers(partner) if cg == '41100000' else ''
        product_label = r['Libellé']  if pd.notna(r['Libellé'])   else None
        partner_name  = r['Partenaire'] if pd.notna(r['Partenaire']) else ''
        raw_lib = str(product_label if product_label else partner_name)
        lib  = raw_lib.replace('\n', ' ').replace(';', ' ').replace('  ', ' ').strip()[:69]
        deb  = fmt_decimal(r['Débit']  if pd.notna(r['Débit'])  else '')
        cre  = fmt_decimal(r['Crédit'] if pd.notna(r['Crédit']) else '')
        date = fmt_date(r['Date'])
        dech = fmt_date(r["Date d'échéance"]) if pd.notna(r["Date d'échéance"]) else date

        base = [
            'VT', date,
            str(r['Numéro']) if pd.notna(r['Numéro']) else '',
            cg, ct, lib, deb, cre, dech
        ]

        # Ligne 411/445 : toujours sans analytique
        if cg.startswith('411') or cg.startswith('445'):
            lines.append(';'.join(base) + ';0;')
        else:
            # Ligne produit (706xxx) : une seule ligne avec code si disponible, sinon 0
            if code:
                lines.append(';'.join(base) + f';1;{code}')
            else:
                lines.append(';'.join(base) + ';0;')

    return '\n'.join(lines)
