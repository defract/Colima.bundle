# Colima - Combined Library Metadata Agent

import logging, re, countrycode

BASE_URL = 'https://api.tmdb.org/3'
API_KEY = '59bb0db203a09d2820a27734437c3bd6'
TMDB_CONFIG = '%s/configuration?api_key=%s' % (BASE_URL, API_KEY)

TMDB_MOVIE_SEARCH = '%s/search/movie?api_key=%s&query=%%s&year=%%s&language=%%s&include_adult=%%s' % (BASE_URL, API_KEY)
TMDB_MOVIE = '%s/movie/%%s?api_key=%s&append_to_response=releases,credits&language=%%s' % (BASE_URL, API_KEY)
TMDB_MOVIE_IMAGES = '%s/movie/%%s/images?api_key=%s' % (BASE_URL, API_KEY)

ARTWORK_ITEM_LIMIT = 15
POSTER_SCORE_RATIO = .3 # How much weight to give ratings vs. vote counts when picking best posters. 0 means use only ratings.
BACKDROP_SCORE_RATIO = .3

# TMDB does not seem to have an official set of supported languages.  Users can register and 'translate'
# any movie to any ISO 639-1 language.  The following is a realistic list from a popular title.
# This agent falls back to English metadata and sorts out foreign artwork to to ensure the best
# user experience when less common languages are chosen.
LANGUAGES = [
             Locale.Language.English, Locale.Language.Czech, Locale.Language.Danish, Locale.Language.German,
             Locale.Language.Greek, Locale.Language.Spanish, Locale.Language.Finnish, Locale.Language.French,
             Locale.Language.Hebrew, Locale.Language.Croatian, Locale.Language.Hungarian, Locale.Language.Italian,
             Locale.Language.Latvian, Locale.Language.Dutch, Locale.Language.Norwegian, Locale.Language.Polish,
             Locale.Language.Portuguese, Locale.Language.Russian, Locale.Language.Slovak, Locale.Language.Swedish,
             Locale.Language.Thai, Locale.Language.Turkish, Locale.Language.Vietnamese, Locale.Language.Chinese,
             Locale.Language.Korean
            ]

##########################################################################################################################################################
# Helper functions
##########################################################################################################################################################

def log (LogMessage):
    if Prefs['debug']:
        Log.Debug(LogMessage)

def GetJSON(url, cache_time=CACHE_1MONTH):
    tmdb_dict = None

    try:
        tmdb_dict = JSON.ObjectFromURL(url, sleep=2.0, headers={'Accept': 'application/json'}, cacheTime=cache_time)
    except:
        log('Error fetching JSON from The Movie Database: %s' % url)

    return tmdb_dict

##########################################################################################################################################################
# Agent code
##########################################################################################################################################################


class Colima(Agent.TV_Shows):
    name = 'Colima'
    languages = LANGUAGES
    primary_provider = True
    fallback_agent = 'com.plexapp.agents.thetvdb'
    accepts_from = ['com.plexapp.agents.localmedia', 'com.plexapp.agents.opensubtitles', 'com.plexapp.agents.plexthememusic', 'com.plexapp.agents.subzero']
    contributes_to = None

    ######################################################################################################################################################
    # Search
    ######################################################################################################################################################

    def search(self, results, media, lang, manual):
        log("".ljust(120, '*'))
        log('>> Search')
        log("".ljust(120, '*'))

        # Get 'Include adult content (Movies)' configuration setting
        include_adult = 'false'
        if Prefs['adult']:
            include_adult = 'true'
        log('adult: ' + include_adult)

        # Get 'Movie path identifcator' configuration setting
        ident = Prefs['movie_ident']
        log('movie_ident: ' + ident)

        # normalize filename
        filename = String.Unquote(media.filename)
        title = media.show

        log("Title: '%s', name: '%s', filename: '%s', manual: '%s', year: '%s'" % (title, media.name, filename, str(manual), media.year))

        if filename.find(ident) == -1:
            log('Could not find movie identifactor. Hand this file over to the TVDB agent (via fallback mechanism).')
            results.Append(MetadataSearchResult(id='', name=title, year=media.year, lang=lang, score=0))
        else:
            log('Movie identifactor found. Find results for it.')

            try:
                # check for year and extract it
                year_match = re.search("\(\d{4}\)$", title)

                if year_match:
                    media.year = year_match.group()[1: -1]
                    media.show = title[0: -7];

                if media.year and int(media.year) > 1900:
                    year = media.year
                else:
                    year = ''
            except Exception as e:
                log('Error: %s' % e)
                pass

            stripped_name = String.StripDiacritics(media.show)
            searchurl = TMDB_MOVIE_SEARCH % (String.Quote(stripped_name), year, lang, include_adult)

            log(searchurl)
            tmdb_dict = GetJSON(url=TMDB_MOVIE_SEARCH % (String.Quote(stripped_name), year, lang, include_adult))
            if media.name != stripped_name and (tmdb_dict == None or len(tmdb_dict['results']) == 0):
                Log('No results for title modified by strip diacritics, searching again with the original: ' + media.show)
                searchurl = TMDB_MOVIE_SEARCH % (String.Quote(media.show), year, lang, include_adult)
                tmdb_dict = GetJSON(url= searchurl)

            if isinstance(tmdb_dict, dict) and 'results' in tmdb_dict:
                for i, movie in enumerate(sorted(tmdb_dict['results'], key=lambda k: k['popularity'], reverse=True)):
                    score = 90
                    score = score - abs(String.LevenshteinDistance(movie['title'].lower(), media.show.lower()))

                    # Adjust score slightly for 'popularity' (helpful for similar or identical titles when no media.year is present)
                    score = score - (5 * i)

                    if 'release_date' in movie and movie['release_date']:
                        release_year = int(movie['release_date'].split('-')[0])
                    else:
                        release_year = -1

                    if media.year and int(media.year) > 1900 and release_year:
                        year_diff = abs(int(media.year) - release_year)

                        if year_diff <= 1:
                            score = score + 10
                        else:
                            score = score - (5 * year_diff)

                    if score <= 0:
                        log('No valid match for movie. Score is 0.')
                        continue
                    else:
                        id = movie['id']
                        results.Append(MetadataSearchResult(id=str(id), name=movie['title'], year=release_year, lang=lang, score=score))


    ######################################################################################################################################################
    # Update
    ######################################################################################################################################################

    def update(self, metadata, media, lang, force):
        log("".ljust(120, '*'))
        log('>> Update')
        log("".ljust(120, '*'))

        # Get all metadata
        config_dict = GetJSON(url=TMDB_CONFIG, cache_time=CACHE_1WEEK * 2)
        tmdb_dict = GetJSON(url=TMDB_MOVIE % (metadata.id, lang))

        if not isinstance(tmdb_dict, dict) or 'overview' not in tmdb_dict or tmdb_dict['overview'] is None or tmdb_dict['overview'] == "":
            # Retry the query with no language specified if we didn't get anything from the initial request.
            tmdb_dict = GetJSON(url=TMDB_MOVIE % (metadata.id, ''))

        tmdb_images_dict = GetJSON(url=TMDB_MOVIE_IMAGES % metadata.id)

        # Title.
        metadata.title = tmdb_dict['title']

        # Rating.
        metadata.rating = tmdb_dict['vote_average']

        # Summary.
        metadata.summary = tmdb_dict['overview']
        if metadata.summary  == 'No overview found.':
            metadata.summary = ""

        if Prefs['country'] != '':
            c = Prefs['country']

            for country in tmdb_dict['releases']['countries']:
                if country['iso_3166_1'] == countrycode.COUNTRY_TO_CODE[c]:

                    # Content rating.
                    if 'certification' in country and country['certification'] != '':
                        if countrycode.COUNTRY_TO_CODE[c] == 'US':
                            metadata.content_rating = country['certification']
                        else:
                            metadata.content_rating = '%s/%s' % (countrycode.COUNTRY_TO_CODE[c].lower(), country['certification'])

                    # Release date (country specific).
                    if 'release_date' in country and country['release_date'] != '':
                        try:
                            metadata.originally_available_at = Datetime.ParseDate(tmdb_dict['release_date']).date()
                        except:
                            pass

                    break

        # Studio.
        try:
            studios = tmdb_dict.get('production_companies', [])
            metadata.studio = studios[0]['name']
        except:
            log('Error while retrieving studio.')
            pass

        # Genres.
        metadata.genres.clear()
        for genre in tmdb_dict.get('genres'):
            metadata.genres.add(genre['name'])

        # Cast.
        try:
            metadata.roles.clear()

            for member in tmdb_dict['credits']['cast']:
                role = metadata.roles.new()
                role.role = member['character']
                role.name = member['name']

                if member['profile_path'] is not None:
                    role.photo = config_dict['images']['base_url'] + 'original' + member['profile_path']

        except Exception as e:
            log('Error while retrieving cast: %s' % e)
            pass

        ##################################################################################################################################################
        # Images
        ##################################################################################################################################################

        try:
            ##############################################################################################################################################
            # Posters
            ##############################################################################################################################################

            log('Fetching posters')
            if tmdb_images_dict['posters']:
                max_average = max([(lambda p: p['vote_average'] or 5)(p) for p in tmdb_images_dict['posters']])
                max_count = max([(lambda p: p['vote_count'])(p) for p in tmdb_images_dict['posters']]) or 1

                for i, poster in enumerate(tmdb_images_dict['posters']):
                    score = (poster['vote_average'] / max_average) * POSTER_SCORE_RATIO
                    score += (poster['vote_count'] / max_count) * (1 - POSTER_SCORE_RATIO)
                    tmdb_images_dict['posters'][i]['score'] = score

                    # Boost the score for localized posters (according to the preference).
                    if Prefs['localart']:
                        if poster['iso_639_1'] == lang:
                            tmdb_images_dict['posters'][i]['score'] = poster['score'] + 1

                    # Discount score for foreign posters.
                    if poster['iso_639_1'] != lang and poster['iso_639_1'] is not None and poster['iso_639_1'] != 'en':
                        tmdb_images_dict['posters'][i]['score'] = poster['score'] - 1

                for i, poster in enumerate(sorted(tmdb_images_dict['posters'], key=lambda k: k['score'], reverse=True)):
                    if i > ARTWORK_ITEM_LIMIT:
                        break
                    else:
                        poster_url = config_dict['images']['base_url'] + 'original' + poster['file_path']
                        thumb_url = config_dict['images']['base_url'] + 'w154' + poster['file_path']

                        if poster_url not in metadata.posters:
                            try:
                                metadata.posters[poster_url] = Proxy.Preview(HTTP.Request(thumb_url).content, sort_order=i + 1)
                            except:
                                pass

                ##########################################################################################################################################
                # Backdrops
                ##########################################################################################################################################
                log('Fetching backdrops')

                if tmdb_images_dict['backdrops']:
                    max_average = max([(lambda p: p['vote_average'] or 5)(p) for p in tmdb_images_dict['backdrops']])
                    max_count = max([(lambda p: p['vote_count'])(p) for p in tmdb_images_dict['backdrops']]) or 1

                    for i, backdrop in enumerate(tmdb_images_dict['backdrops']):
                        score = (backdrop['vote_average'] / max_average) * BACKDROP_SCORE_RATIO
                        score += (backdrop['vote_count'] / max_count) * (1 - BACKDROP_SCORE_RATIO)
                        tmdb_images_dict['backdrops'][i]['score'] = score

                        # For backdrops, we prefer "No Language" since they're intended to sit behind text.
                        if backdrop['iso_639_1'] == 'xx' or backdrop['iso_639_1'] == 'none':
                            tmdb_images_dict['backdrops'][i]['score'] = float(backdrop['score']) + 2

                        # Boost the score for localized art (according to the preference).
                        if Prefs['localart']:
                            if backdrop['iso_639_1'] == lang:
                                tmdb_images_dict['backdrops'][i]['score'] = float(backdrop['score']) + 1

                        # Discount score for foreign art.
                        if backdrop['iso_639_1'] != lang and backdrop['iso_639_1'] is not None and backdrop['iso_639_1'] != 'en':
                            tmdb_images_dict['backdrops'][i]['score'] = float(backdrop['score']) - 1

                    for i, backdrop in enumerate(sorted(tmdb_images_dict['backdrops'], key=lambda k: k['score'], reverse=True)):
                        if i > ARTWORK_ITEM_LIMIT:
                            break
                        else:
                            backdrop_url = config_dict['images']['base_url'] + 'original' + backdrop['file_path']
                            thumb_url = config_dict['images']['base_url'] + 'w300' + backdrop['file_path']

                            if backdrop_url not in metadata.art:
                                try:
                                    metadata.art[backdrop_url] = Proxy.Preview(HTTP.Request(thumb_url).content, sort_order=i + 1)
                                except:
                                    pass
        except Exception as e:
            log('Error while fetching images: %s' % e)

        ##################################################################################################################################################
        # Set 'Season' metadata
        ##################################################################################################################################################

        for s in media.seasons:
            metadata.seasons[s].index = int(s)

            for e in media.seasons[s].episodes:
                episodeMetadata = metadata.seasons[s].episodes[e]

                # Title.
                episodeMetadata.title = tmdb_dict['title']

                # Summary.
                episodeMetadata.summary = tmdb_dict['overview']

                # Release date.
                try:
                    episodeMetadata.originally_available_at = Datetime.ParseDate(tmdb_dict['release_date']).date()
                except:
                    log('Error while retrieving release date for episode.')
                    pass

                # Rating.
                episodeMetadata.rating = tmdb_dict['vote_average']

                # Director + Writers.
                episodeMetadata.directors.clear()
                episodeMetadata.writers.clear()

                try:
                    for member in tmdb_dict['credits']['crew']:
                        if member['job'] == 'Director':
                            director = episodeMetadata.directors.new()
                            director.name = member['name']
                        elif member['job'] in ('Writer', 'Screenplay', 'Author', 'Novel'):
                            writer = episodeMetadata.writers.new()
                            writer.name = member['name']
                except:
                    log('Error while retrieving directors and writers for episode.')
                    pass
