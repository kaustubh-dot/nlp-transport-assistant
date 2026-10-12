"""Small adapters over the existing snapshot services, with explicit options."""
from itertools import product


def published_route_options(service, matches: list[dict], slots: dict, execution: dict, catalog: dict) -> tuple[list[dict], bool]:
    """Show matching boarding/alighting options; do not select an ambiguous ID."""
    requested = slots.get('transport_mode')
    requested_modes = {'suburban_rail', 'mrts'} if requested == 'rail' else {requested} if requested else None
    endpoints = {}
    for role in ('origin', 'destination'):
        candidates = {row['entity_id']: row for match in matches if match['value'] == slots.get(role)
                      for row in match['candidates'] if row['kind'] == 'stop'}
        # Reviewed example boarding candidates retain their own names/IDs.
        # They are an option near the named context, not a verified transfer.
        local = next((row for row in catalog['locations'] if row['id'] == slots.get(role)), {})
        for candidate in local.get('boarding_candidates', []):
            candidates[candidate['entity_id']] = candidate
        endpoints[role] = [row for row in candidates.values() if not requested_modes or row['mode'] in requested_modes]
    pairs = [(a, b) for a, b in product(endpoints['origin'], endpoints['destination']) if a['mode'] == b['mode']]
    routes = {}
    for origin, destination in pairs[:64]:
        arguments = dict(execution, origin=origin['entity_id'], destination=destination['entity_id'], transport_mode=origin['mode'])
        answer = service.execute('PLAN_ROUTE', arguments)
        if answer.status != 'ok':
            continue
        for row in answer.data['routes']:
            key = (row['route_id'], row['direction_id'], row['origin_stop_id'], row['destination_stop_id'])
            routes[key] = row
    ordered = sorted(routes.values(), key=lambda row: (row['route_name'], row['origin_stop_id'], row['destination_stop_id']))
    return ordered[:10], len(pairs) > 64 or len(routes) > 10


def curated_journey_guidance(catalog: dict, matches: list[dict], slots: dict) -> list[dict]:
    mode = slots.get('transport_mode')
    found = []
    for row in catalog.get('journey_guidance', []):
        if mode is not None and mode not in row['accepted_modes']:
            continue
        for role in ('origin', 'destination'):
            location = row.get(role + '_location')
            stop = row.get(role + '_stop_id')
            if location and slots.get(role) != location:
                break
            if stop and not any(candidate['entity_id'] == stop for match in matches if match['value'] == slots.get(role)
                                for candidate in match['candidates']):
                break
        else:
            found.append(row)
    return found
