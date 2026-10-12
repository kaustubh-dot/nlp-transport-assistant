"""Small, escaped presentation helpers for the academic Streamlit demo."""
from html import escape
from urllib.parse import urlparse


def e(value):
    return escape(str(value), quote=True)


def masthead(hi):
    title = 'रास्ता पूछिए।' if hi else 'Rasta poochhiye.'
    description = ('चेन्नई में रास्ता, स्टेशन या सुविधा — अपने शब्दों में पूछें।' if hi else
                   'Chennai mein route, station ya facility — apne shabdon mein poochhein.')
    return (f'<header class="transit-masthead"><div class="transit-wordmark">Chennai Transit</div>'
            f'<span class="transit-edition">HINDI / HINGLISH · NLP DEMO</span>'
            f'<h1>{title}</h1><p>{description}</p></header>')


def sidebar_brand():
    return '<div class="transit-rail-brand">Chennai<br>Transit<span>TRANSPORT NLP PROJECT</span></div>'


def entity_ledger(slots, hi):
    labels = {
        'origin': ('कहाँ से', 'Kahan se'), 'destination': ('कहाँ तक', 'Kahan tak'),
        'station': ('स्टेशन', 'Station'), 'transport_mode': ('माध्यम', 'Mode'),
        'station_detail': ('जानकारी', 'Information'), 'information_type': ('जानकारी', 'Information'),
        'accessibility_feature': ('सुविधा', 'Facility'), 'complaint_type': ('शिकायत', 'Complaint'),
    }
    rows = []
    values = {
        'nearby_bus': ('पास के बस स्टॉप', 'Nearby bus stops'),
        'nearby_transport': ('पास के परिवहन विकल्प', 'Nearby transport'),
        'first_service': ('पहली सेवा', 'First service'), 'last_service': ('आखिरी सेवा', 'Last service'),
        'lift': ('लिफ्ट', 'Lift'), 'wheelchair': ('व्हीलचेयर', 'Wheelchair'),
    }
    for key, value in slots.items():
        label = labels.get(key, (key.replace('_', ' '), key.replace('_', ' ')))[0 if hi else 1]
        value = ', '.join(str(item) for item in value) if isinstance(value, list) else value
        value = values.get(value, (value, value))[0 if hi else 1]
        rows.append(f'<div><dt>{e(label)}</dt><dd>{e(value)}</dd></div>')
    return '<dl class="transit-ledger">' + ''.join(rows) + '</dl>'


def record_overview(result, names, hi):
    """Show only fields supplied by lookup; never synthesize travel directions."""
    if result['status'] != 'information':
        return ''
    records = result.get('records', [])
    nearby = [row for row in records if row.get('type') in ('canonical_nearby_bus', 'canonical_nearby_transport')]
    if nearby:
        rows = []
        seen = set()
        for row in sorted(nearby, key=lambda item: item['distance_m']):
            marker = (row['name'].casefold(), row['mode'])
            if marker in seen:
                continue
            seen.add(marker)
            rows.append(f'<li><span>{e(row["name"])}<small>{e(row["mode"])}</small></span>'
                        f'<strong>{e(round(row["distance_m"]))} m</strong></li>')
        note = 'सीधी दूरी · पैदल चलने का रास्ता नहीं' if hi else 'Seedhi doori · walking route nahi'
        return '<ul class="transit-stop-list">' + ''.join(rows) + f'</ul><p class="transit-data-note">{note}</p>'
    published = [row for row in records if row.get('stop_names')]
    if published:
        rows = ''.join(f'<li><span>{e(name)}</span></li>' for row in published for name in row['stop_names'])
        note = 'प्रकाशित प्रवेश जानकारी · दूरी उपलब्ध नहीं' if hi else 'Published entrance information · distance available nahi'
        return f'<ul class="transit-stop-list">{rows}</ul><p class="transit-data-note">{note}</p>'
    slots = result.get('entities', {})
    origin, destination = slots.get('origin'), slots.get('destination')
    if origin and destination and records:
        # This is a summary of the question, not a claim of a direct service.
        start, end = names.get(origin, origin), names.get(destination, destination)
        label = 'आपका सफ़र' if hi else 'Aapka safar'
        detail = ''
        boarding = next((row.get('boarding_stop') or names.get(row.get('boarding_stop_id')) for row in records
                         if row.get('boarding_stop') or row.get('boarding_stop_id')), None)
        if boarding:
            detail = f'<p class="transit-data-note">{"बोर्डिंग स्टेशन" if hi else "Boarding station"}: {e(boarding)}</p>'
        return (f'<div class="transit-journey"><span class="transit-data-note">{label}</span>'
                f'<div><strong>{e(start)}</strong><span aria-label="to">→</span><strong>{e(end)}</strong></div>'
                f'</div>{detail}')
    return ''


def source_title(source):
    if not source.startswith('https://'):
        return 'Chennai transport · local data snapshot'
    host = urlparse(source).hostname or ''
    if host.endswith('chennaimetrorail.org'):
        return 'Chennai Metro · published information'
    if host.endswith('indianrailways.gov.in'):
        return 'Southern Railway · published MRTS guide'
    if host == 'github.com':
        return 'Chennai GTFS · community data'
    return host


def source_links(sources):
    rows = []
    for source in dict.fromkeys(sources):
        label = e(source_title(source))
        if source.startswith('https://'):
            rows.append(f'<a href="{e(source)}" target="_blank" rel="noopener noreferrer">{label} ↗</a>')
        else:
            rows.append(f'<span>{label}</span>')
    return '<div class="transit-sources">' + ''.join(rows) + '</div>' if rows else ''
