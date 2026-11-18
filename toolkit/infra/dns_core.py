import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import doh

ZONE = 'onlyfakeai.ru'
REF = '<supabase-project-ref>'

core = [
    (ZONE, 'A'), (ZONE, 'AAAA'), (ZONE, 'NS'), (ZONE, 'MX'), (ZONE, 'TXT'),
    (ZONE, 'SOA'), (ZONE, 'CAA'), (ZONE, 'DNSKEY'), (ZONE, 'HTTPS'),
    ('www.' + ZONE, 'A'), ('www.' + ZONE, 'CNAME'),
    ('ops.' + ZONE, 'A'), ('ops.' + ZONE, 'AAAA'), ('ops.' + ZONE, 'CNAME'),
    ('cdn.' + ZONE, 'A'), ('cdn.' + ZONE, 'AAAA'), ('cdn.' + ZONE, 'CNAME'),
    ('cdn.' + ZONE, 'TXT'),
    ('_dmarc.' + ZONE, 'TXT'),
    ('_acme-challenge.' + ZONE, 'TXT'),
    ('_acme-challenge.www.' + ZONE, 'TXT'),
    ('_acme-challenge.ops.' + ZONE, 'TXT'),
    ('_acme-challenge.cdn.' + ZONE, 'TXT'),
    ('_supabase.' + ZONE, 'TXT'),
    ('supabase.' + ZONE, 'A'),
    ('db.' + ZONE, 'A'),
    ('pooler.' + ZONE, 'A'),
    ('_vercel.' + ZONE, 'TXT'),
    ('_github-pages-challenge-' + 'onlyfakeai.' + ZONE, 'TXT'),
    ('resend._domainkey.' + ZONE, 'TXT'),
    ('default._domainkey.' + ZONE, 'TXT'),
    ('google._domainkey.' + ZONE, 'TXT'),
    ('dkim._domainkey.' + ZONE, 'TXT'),
    ('mail._domainkey.' + ZONE, 'TXT'),
    ('s1._domainkey.' + ZONE, 'TXT'),
    ('s2._domainkey.' + ZONE, 'TXT'),
    ('selector1._domainkey.' + ZONE, 'TXT'),
    ('selector2._domainkey.' + ZONE, 'TXT'),
    ('k1._domainkey.' + ZONE, 'TXT'),
    ('sendgrid._domainkey.' + ZONE, 'TXT'),
    ('mailgun._domainkey.' + ZONE, 'TXT'),
    ('postmark._domainkey.' + ZONE, 'TXT'),
    ('smtp._domainkey.' + ZONE, 'TXT'),
    ('send._domainkey.' + ZONE, 'TXT'),
    ('v1._domainkey.' + ZONE, 'TXT'),
    ('v2._domainkey.' + ZONE, 'TXT'),
    (REF + '.supabase.co', 'A'),
    (REF + '.supabase.co', 'AAAA'),
    (REF + '.supabase.co', 'CNAME'),
    ('db.' + REF + '.supabase.co', 'A'),
    ('db.' + REF + '.supabase.co', 'AAAA'),
    ('db.' + REF + '.supabase.co', 'CNAME'),
    ('pooler.' + REF + '.supabase.co', 'A'),
    (REF + '.supabase.in', 'A'),
]

for name, rtype in core:
    rec = doh.query(name, rtype)
    doh.log(rec, 'dns_core')
    print(doh.summarize(rec))
