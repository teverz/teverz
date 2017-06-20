import os
import re
import time

import kodi
import log_utils  # @UnusedImport
from salts_lib import utils2
from salts_lib.constants import FORCE_NO_MATCH
from salts_lib.constants import VIDEO_TYPES

__all__ = ['scraper', 
 'proxy', 
 'local_scraper', 
#'2ddl_scraper', 
#'afdah_scraper', 
#'afdahorg_scraper', 
#'alluc_scraper', 
#'apollo_proxy', 
 'dayt_scraper', 
 'ddlseries_scraper', 
 'ddlvalley_scraper', 
 'directdl_scraper', 
 'dizigold_scraper', 
#'dizimag_scraper', 
#'downloadtube_scraper', 
 'emoviespro_scraper', 
#'farda_scraper', 
#'filmikz_scraper', 
 'filmovizjia_scraper', 
#'fmovie_scraper', 
#'hdflix_scraper', 
#'hdmovie14_scraper', 
 'hdmoviefree_scraper', 
 'hevcbluray_scraper', 
#'heydl_scraper', 
 'icefilms_scraper', 
 'iwatch_scraper', 
#'kohi_scraper', 
#'m4ufree_scraper', 
 'mintmovies_scraper', 
#'miradetodo_scraper', 
 'movie25_scraper', 
#'movieflix_scraper', 
 'moviego_scraper', 
 'moviehubs_scraper', 
#'moviepool_scraper', 
#'movieshd_scraper', 
#'moviestorm_scraper', 
 'moviesub_scraper', 
 'movietube_scraper', 
 'moviewatcher_scraper', 
#'moviexk_scraper', 
#'moviezone_scraper', 
#'movytvy_scraper', 
#'myvideolinks_scraper', 
#'oneclicktvshows_scraper', 
#'ororotv_scraper', 
#'ol_scraper', 
 'pelispedia_scraper', 
 'pftv_scraper', 
 'piratejunkies_scraper', 
#'pubfilm_scraper', 
#'putlocker_scraper', 
 'putmv_scraper', 
 'pw_scraper', 
 'quikr_scraper', 
#'rainierland_scraper', 
#'real_scraper', 
 'rlsbb_scraper', 
#'rlssource_scraper', 
 'scenedown_scraper', 
 'scenerls_scraper', 
 'serieswatch_scraper', 
 'sezonlukdizi_scraper', 
#'solar_scraper', 
#'spacemov_scraper', 
#'tunemovie_scraper', 
 'tvonline_scraper', 
 'tvrush_scraper', 
#'vebup_scraper', 
#'ventures_scraper', 
 'vidics_scraper', 
 'viooz_scraper', 
 'vivoto_scraper', 
#'vu45_scraper', 
#'watch5s_scraper', 
 'watchfree_scraper', 
 'watchitvideos_scraper', 
#'watchonline_scraper', 
 'watchseries_scraper', 
 'xmovies8_scraper', 
 'xmovies8v2_scraper', 
 'yesmovies_scraper']
#'yshows_scraper']

from . import *

logger = log_utils.Logger.get_logger()
  
class ScraperVideo:
    def __init__(self, video_type, title, year, trakt_id, season='', episode='', ep_title='', ep_airdate=''):
        assert(video_type in (VIDEO_TYPES.__dict__[k] for k in VIDEO_TYPES.__dict__ if not k.startswith('__')))
        self.video_type = video_type
        if isinstance(title, unicode): self.title = title.encode('utf-8')
        else: self.title = title
        self.year = str(year)
        self.season = season
        self.episode = episode
        if isinstance(ep_title, unicode): self.ep_title = ep_title.encode('utf-8')
        else: self.ep_title = ep_title
        self.trakt_id = trakt_id
        self.ep_airdate = utils2.to_datetime(ep_airdate, "%Y-%m-%d").date() if ep_airdate else None

    def __str__(self):
        return '|%s|%s|%s|%s|%s|%s|%s|' % (self.video_type, self.title, self.year, self.season, self.episode, self.ep_title, self.ep_airdate)

def update_xml(xml, new_settings, cat_count):
    new_settings.insert(0, '<category label="Scrapers %s">' % (cat_count))
    new_settings.append('    </category>')
    new_settings = '\n'.join(new_settings)
    match = re.search('(<category label="Scrapers %s">.*?</category>)' % (cat_count), xml, re.DOTALL | re.I)
    if match:
        old_settings = match.group(1)
        if old_settings != new_settings:
            xml = xml.replace(old_settings, new_settings)
    else:
        logger.log('Unable to match category: %s' % (cat_count), log_utils.LOGWARNING)
    return xml

def update_settings():
    full_path = os.path.join(kodi.get_path(), 'resources', 'settings.xml')
    
    try:
        # open for append; skip update if it fails
        with open(full_path, 'a') as f:
            pass
    except Exception as e:
        logger.log('Dynamic settings update skipped: %s' % (e), log_utils.LOGWARNING)
    else:
        with open(full_path, 'r') as f:
            xml = f.read()

        new_settings = []
        cat_count = 1
        old_xml = xml
        classes = scraper.Scraper.__class__.__subclasses__(scraper.Scraper)  # @UndefinedVariable
        classes += proxy.Proxy.__class__.__subclasses__(proxy.Proxy)  # @UndefinedVariable
        for cls in sorted(classes, key=lambda x: x.get_name().upper()):
            if not cls.get_name() or cls.has_proxy(): continue
            new_settings += cls.get_settings()
            if len(new_settings) > 90:
                xml = update_xml(xml, new_settings, cat_count)
                new_settings = []
                cat_count += 1
    
        if new_settings:
            xml = update_xml(xml, new_settings, cat_count)
    
        if xml != old_xml:
            with open(full_path, 'w') as f:
                f.write(xml)
        else:
            logger.log('No Settings Update Needed', log_utils.LOGDEBUG)


def update_all_scrapers():
        try: last_check = int(kodi.get_setting('last_list_check'))
        except: last_check = 0
        now = int(time.time())
        list_url = kodi.get_setting('scraper_url')
        scraper_password = kodi.get_setting('scraper_password')
        list_path = os.path.join(kodi.translate_path(kodi.get_profile()), 'scraper_list.txt')
        exists = os.path.exists(list_path)
        if list_url and scraper_password and (not exists or (now - last_check) > 15 * 60):
            _etag, scraper_list = utils2.get_and_decrypt(list_url, scraper_password)
            if scraper_list:
                try:
                    with open(list_path, 'w') as f:
                        f.write(scraper_list)
    
                    kodi.set_setting('last_list_check', str(now))
                    kodi.set_setting('scraper_last_update', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now)))
                    for line in scraper_list.split('\n'):
                        line = line.replace(' ', '')
                        if line:
                            scraper_url, filename = line.split(',')
                            if scraper_url.startswith('http'):
                                update_scraper(filename, scraper_url)
                except Exception as e:
                    logger.log('Exception during scraper update: %s' % (e), log_utils.LOGWARNING)
    
def update_scraper(filename, scraper_url):
    try:
        if not filename: return
        py_path = os.path.join(kodi.get_path(), 'scrapers', filename)
        exists = os.path.exists(py_path)
        scraper_password = kodi.get_setting('scraper_password')
        if scraper_url and scraper_password:
            old_etag = ''
            old_py = ''
            if exists:
                with open(py_path, 'r') as f:
                    old_py = f.read()
                    match = re.search('^#\s+Etag:\s*(.*)', old_py)
                    if match:
                        old_etag = match.group(1).strip()

            new_etag, new_py = utils2.get_and_decrypt(scraper_url, scraper_password, old_etag)
            if new_py:
                logger.log('%s path: %s, new_py: %s, match: %s' % (filename, py_path, bool(new_py), new_py == old_py), log_utils.LOGDEBUG)
                if old_py != new_py:
                    with open(py_path, 'w') as f:
                        f.write('# Etag: %s\n' % (new_etag))
                        f.write(new_py)
                    kodi.notify(msg=utils2.i18n('scraper_updated') + filename)
                        
    except Exception as e:
        logger.log('Failure during %s scraper update: %s' % (filename, e), log_utils.LOGWARNING)

update_settings()
update_all_scrapers()
