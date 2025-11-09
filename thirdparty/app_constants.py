


# --- GraphQL Queries ---
SEARCH_TITLES_QUERY = """
query GetSearchTitles(
    $searchTitlesFilter: TitleFilter!,
    $country: Country!,
    $language: Language!,
    $first: Int!
    $sortBy: PopularTitlesSorting!,
) {
    popularTitles(
    country: $country
    filter: $searchTitlesFilter
    first: $first
    sortBy: $sortBy
    sortRandomSeed: 0
    ) {
    edges {
        node {
        id
        objectType
        content(country: $country, language: $language) {
            title
            shortDescription
            originalReleaseYear
            originalReleaseDate
            runtime
            genres {
            shortName
            }
            externalIds {
            imdbId
            tmdbId
            }
            ageCertification
            posterUrl
            backdrops {
                backdropUrl
            }
        }
        }
    }
    }
}
"""

SEARCH_RELEASE_QUERY = """
query SearchNewTitles(
$country: Country!
$language: Language!
$first: Int!
) {
newTitles(country: $country, first: $first) {
    edges {
    node {
        id
        content(country: $country, language: $language) {
        ... on MovieContent {
            title
            shortDescription
            originalReleaseYear
            originalReleaseDate
            runtime
            genres {
                shortName
            }
            externalIds {
                imdbId
                tmdbId
            }
            ageCertification
        }
        }
    }
    }
}
}
"""

DETAILS_QUERY = """
query GetTitleNode($nodeId: ID!, $country: Country!, $language: Language!) {
    node(id: $nodeId) {
    ... on MovieOrShow {
        id
        objectType
        content(country: $country, language: $language) {
        title
        shortDescription
        originalReleaseYear
        runtime
        genres {
            shortName
        }
        externalIds {
            imdbId
            tmdbId
        }
        ageCertification
        scoring {
            imdbScore
            tmdbScore
            jwRating
        }
        }
    }
    }
}
"""

GENRE_MAPPING = {
    'act': 'Action & Adventure',
    'ani': 'Animation',
    'cmy': 'Comedy',
    'crm': 'Crime',
    'doc': 'Documentary',
    'drm': 'Drama',
    'fnt': 'Fantasy',
    'hst': 'History',
    'hrr': 'Horror',
    'fml': 'Kids & Family',
    'msc': 'Music & Musical',
    'trl': 'Mystery & Thriller',
    'rma': 'Romance',
    'scf': 'Science-Fiction',
    'spt': 'Sport',
    'war': 'War & Military',
    'wsn': 'Western',
    'rly': 'Reality TV',
    'eur': 'Made in Europe'
}
