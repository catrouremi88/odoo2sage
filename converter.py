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

# ── Codes clients Sage pour les filiales ─────────────────────────────────────
FILIALE_SAGE_CODE = {
    'ALTIOS FRANCE SAS':                                        '411ALTFR',
    'ALTIOS SOUTH EAST ASIA PRIVATE LIMITED':                   '411ALTSI',
    'ALTIOS CORPORATE SERVICES SAS':                            '411ACS',
    'ALTIOS INTERNATIONAL SAS':                                 '411ALTINT',
    'ALTIOS MALAYSIA SDN BHD':                                  '411ALTMAL',
    'ALTIOS GERMANY GMBH':                                      '411ALTALL',
    'ALTIOS POLSKA S.P.Z.O.O.':                                 '411LOGOS',
    'ALTIOS INTERNATIONAL UK LIMITED':                          '411FRENGERBUS',
    'FRENGER BUSINESS SERVICES LIMITED':                        '411FRENGERBUS',
    'FRENGER CONSULTING SERVICES LIMITED':                      '411FRENGERBUS',
    'ALTIOS SPAIN SOCIEDAD LIMITADA':                           '411ALTESP',
    'LUSIALTIOS UNIPESSOAL LDA':                                '411ALTPOR',
    'ALTIOS ITALIA SRL':                                        '411ALTIT',
    'ALTIOS ASIA LIMITED':                                      '411ALTAS',
    'ALTIOS HONG-KONG LIMITED':                                 '411ALTHK',
    'ALTIOS AUSTRALIA PTY LIMITED':                             '411ALTAU',
    'ALTIOS NEW ZEALAND LIMITED':                               '411ALTNZ',
    'ALTIOS INTERNATIONAL INC':                                 '411ALTUS',
    'ALTIOS CONSEILS INC':                                      '411ALTCAN',
    'ALTIOS ADVISORY MEXICO S.A DE C.V':                        '411ALTME',
    'ALTIOS LATAM SERVICES S.A DE C.V':                         '411ALTMELAT',
    'ALTIOS DO BRASIL CONSULTORIA E REPRESENTACOES LTDA':       '411ALTBRE',
    'ALTIOS INTERNATIONAL FZCO':                                '411STEERING',
    'M AND V MARKETING AND SALES PRIVATE LIMITED':              '411MNS',
    'M AND V MARKETING DEVELOPMENT SERVICES PRIVATE LIMITED':   '411MDS',
    'M&V MARKET DEVELOPMENT SERVICE PVT. LTD':                  '411MNS',
    'GRUPO LT COLOMBIA SAS':                                    '411ALTCOLHOLD',
}


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
    upper = str(partner).strip().upper()
    # Code Sage officiel si filiale connue
    if upper in FILIALE_SAGE_CODE:
        return FILIALE_SAGE_CODE[upper]
    # Sinon génération automatique : 411 + alphanumérique tronqué à 14 chars
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

    # Normaliser les noms de colonnes (FR et EN)
    col_map = {
        'Partner':       'Partenaire',
        'Account':       'Compte',
        'Debit':         'Débit',
        'Credit':        'Crédit',
        'Due Date':      "Date d'échéance",
        'Label':         'Libellé',
        'Reference':     'Référence',
        'Number':        'Numéro',
        'Journal Entry': 'Pièce comptable',
    }
    df = df.rename(columns=col_map)

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

        # Date d'échéance : uniquement sur les lignes 411
        if cg.startswith('411') or cg.startswith('445'):
            base_dech = dech
        else:
            base_dech = ''

        base = [
            'VT', date,
            re.sub(r'[^0-9]', '', str(r['Numéro'])) if pd.notna(r['Numéro']) else '',
            cg, ct, lib, deb, cre, base_dech
        ]

        # Ligne 411/445 : une seule ligne G sans analytique
        if cg.startswith('411') or cg.startswith('445'):
            lines.append(';'.join(base) + ';G;0;')
        else:
            # Ligne produit : ligne G puis ligne A avec code section
            lines.append(';'.join(base) + ';G;0;')
            lines.append(';'.join(base) + f';A;1;{code}')

    return '\n'.join(lines)
