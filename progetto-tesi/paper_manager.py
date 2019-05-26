from logging import warning

from scopus import AbstractRetrieval, ScopusSearch

from models import Paper


# IMPROVE: use API 'field' attribute to only return used fileds


def get_papers(conference):
    # IMPROVE: filtrare i risultati tramite levenshtein, vedere se sono conference
    # o journals (quindi vol. o anno) e vedere se l'anno va bene come filtro
    # IMPROVE: non tutte le conferences sono listate in scopus, ma possono avere
    # le paper. es: https://dblp.org/db/conf/securecomm/securecomm2016.html
    # quindi cercare anche su dblp le conference e cercare le paper su scopus
    # TODO: refactor this method using the conference info from CONFNAME
    query = f"SRCTITLE({conference.getattr('acronym')}) \
              AND PUBYEAR = {conference.getattr('year')}"

    documents = ScopusSearch(query, view="STANDARD")
    papers = [Paper(scopus_id=sid) for sid in documents.get_eids()]
    return papers


def extract_references_from_paper(paper):
    try:
        # FIXME: remove refresh=True when the following issue is resolved:
        # https://github.com/scopus-api/scopus/issues/99
        references = AbstractRetrieval(paper.scopus_id, view="REF", refresh=True).references
    except Exception:
        warning('Retrieval of references failed for eid ' + paper.scopus_id)
        return []

    if not references:
        return []

    eids = [f"9-s2.0-{auid.strip()}" for ref in references if ref.authors_auid
            for auid in ref.authors_auid.split('; ')]
    return eids