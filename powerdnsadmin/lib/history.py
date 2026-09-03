import logging


logger = logging.getLogger(__name__)


def normalize_rrset(rrset):
    """Return an RRset with a safe, list-valued comments field."""
    if not isinstance(rrset, dict) or not rrset:
        if rrset is not None:
            logger.warning('Ignoring invalid RRset value')
        return None

    normalized_rrset = dict(rrset)
    comments = normalized_rrset.get('comments')
    if comments is None:
        normalized_rrset['comments'] = []
    elif not isinstance(comments, list):
        logger.warning('Ignoring invalid RRset comments value')
        normalized_rrset['comments'] = []

    return normalized_rrset


def normalize_history_detail(detail):
    """Normalize RRsets in a decoded history detail without mutating it."""
    normalized_detail = dict(detail)
    for key in ('add_rrsets', 'del_rrsets'):
        rrsets = normalized_detail.get(key) or []
        if not isinstance(rrsets, list):
            logger.warning('Ignoring invalid history RRsets value')
            rrsets = []
        normalized_detail[key] = [
            normalized_rrset for rrset in rrsets
            if (normalized_rrset := normalize_rrset(rrset)) is not None
        ]
    return normalized_detail


def get_records(rrset):
    """Return records with comments paired by their RRset index."""
    rrset = normalize_rrset(rrset)
    if not rrset:
        return []

    records = rrset.get('records') or []
    comments = rrset['comments']
    normalized_records = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            continue

        normalized_record = dict(record)
        normalized_record['comment'] = (
            comments[index].get('content')
            if index < len(comments) and isinstance(comments[index], dict)
            else None
        )
        normalized_records.append(normalized_record)
    return normalized_records
