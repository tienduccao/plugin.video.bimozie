# -*- coding: utf-8 -*-
import sys
import os
import urllib
import urlparse
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmc
import json
from importlib import import_module

# import urlresolver

ADDON = xbmcaddon.Addon()
HANDLE = int(sys.argv[1])
BASEURL = sys.argv[0]
ARGS = urlparse.parse_qs(sys.argv[2][1:])
ADDON_ID = ADDON.getAddonInfo('id')

SITES = [{
    'name': 'bilutv.net',
    'logo': 'http://media.bilutv.net/images/logo.png',
    'class': 'Bilutv',
    'plugin': 'bilutv.plugin'
}, {
    'name': 'phimmedia.tv',
    'logo': 'http://www.phimmedia.tv/templates/themes/phim/images/phimmedia-s.png',
    'class': 'Phimmedia',
    'plugin': 'phimmedia.plugin'
}, {
    'name': 'phimmoi.net',
    'logo': 'http://www.phimmoi.net/logo/phimmoi-square.png',
    'class': 'Phimmoi',
    'plugin': 'phimmoi.plugin'
}, {
    'name': 'tvhay.org',
    'logo': 'http://www.phimmoi.net/logo/phimmoi-square.png',
    'class': 'Tvhay',
    'plugin': 'tvhay.plugin'
}]

addon_data_dir = os.path.join(xbmc.translatePath('special://userdata/addon_data').decode('utf-8'), ADDON_ID)
if not os.path.exists(addon_data_dir):
    os.makedirs(addon_data_dir)


def build_url(query):
    """build the plugin url"""
    return BASEURL + '?' + urllib.urlencode(query)


def onInit():
    xbmcplugin.setPluginCategory(HANDLE, 'My Video Collection')
    xbmcplugin.setContent(HANDLE, 'movies')
    for site in SITES:
        list_item = xbmcgui.ListItem(label=site['name'])
        list_item.setArt({'thumb': site['logo'], 'icon': site['logo']})
        url = build_url({'mode': 'category', 'module': site['plugin'], 'class': site['class']})
        is_folder = True
        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, is_folder)

    xbmcplugin.endOfDirectory(HANDLE, cacheToDisc=True)


def list_category(cats, module, classname):
    xbmcplugin.setPluginCategory(HANDLE, 'Categories')
    xbmcplugin.setContent(HANDLE, 'files')

    # show search link
    url = build_url({'mode': 'search', 'module': module, 'class': classname})
    xbmcplugin.addDirectoryItem(HANDLE, url,
                                xbmcgui.ListItem(label="[COLOR green][B] %s [/B][/COLOR]" % "Search ..."), True)

    for cat in cats:
        list_item = xbmcgui.ListItem(label=cat['title'])
        if 'subcategory' in cat and len(cat['subcategory']) > 0:
            url = build_url({'mode': 'category', 'url': cat['link'], 'name': cat['title'],
                             'subcategory': json.dumps(cat['subcategory']), 'module': module, 'class': classname})
        else:
            url = build_url({'mode': 'movies', 'url': cat['link'], 'page': 1, 'module': module, 'class': classname})
        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, isFolder=True)

    xbmcplugin.endOfDirectory(HANDLE)


def list_movie(movies, link, page, module, classname):
    xbmcplugin.setPluginCategory(HANDLE, 'Categories')
    xbmcplugin.setContent(HANDLE, 'movies')

    if movies is not None:
        for item in movies['movies']:
            list_item = xbmcgui.ListItem(label=item['label'])
            list_item.setLabel2(item['realtitle'])
            list_item.setIconImage('DefaultVideo.png')
            list_item.setArt({
                'thumb': item['thumb'],
            })
            url = build_url(
                {'mode': 'movie', 'url': item['id'], 'thumb': item['thumb'], 'title': item['title'],
                 'module': module, 'class': classname})
            is_folder = True
            xbmcplugin.addDirectoryItem(HANDLE, url, list_item, is_folder)

        print("***********************Current page %d" % page)
        # show next page
        if movies['page'] > 1 and page < movies['page']:
            label = "Next page %d / %d >>" % (page, movies['page'])
            next_item = xbmcgui.ListItem(label=label)
            if 'page_patten' in movies and movies['page_patten'] is not None:
                link = movies['page_patten']

            url = build_url({'mode': 'movies', 'url': link, 'page': page + 1, 'module': module, 'class': classname})
            xbmcplugin.addDirectoryItem(HANDLE, url, next_item, True)
    else:
        return
    xbmcplugin.endOfDirectory(HANDLE)


def show_episode(movie, thumb, title, module, classname):
    if len(movie['episode']) > 0:
        for item in movie['episode']:
            list_item = xbmcgui.ListItem(label=item['title'])
            list_item.setIconImage('DefaultVideo.png')
            list_item.setArt({'thumb': thumb})
            url = build_url({'mode': 'links', 'title': title, 'thumb': thumb, 'url': item['link'], 'module': module,
                             'class': classname})
            is_folder = True
            xbmcplugin.addDirectoryItem(HANDLE, url, list_item, is_folder)

    elif len(movie['group']) > 0:
        for key, items in movie['group'].iteritems():
            xbmcplugin.addDirectoryItem(HANDLE, None,
                                        xbmcgui.ListItem(label="[COLOR red][B] [---- %s ----] [/B][/COLOR]" % key),
                                        False)
            for item in items:
                li = xbmcgui.ListItem(label=item['title'])
                li.setArt({'thumb': thumb})
                li.setProperty('IsPlayable', 'False')
                url = build_url({'mode': 'links', 'title': title, 'thumb': thumb, 'url': item['link'], 'module': module,
                                 'class': classname})
                xbmcplugin.addDirectoryItem(HANDLE, url, li, True)
    else:
        return

    xbmcplugin.setPluginCategory(HANDLE, title)
    xbmcplugin.setContent(HANDLE, 'movies')
    xbmcplugin.endOfDirectory(HANDLE)


def show_links(movie, title, thumb, module, classname):
    if len(movie['links']) == 0:
        return
    elif len(movie['links']) == 1:
        title = "%s - %s" % (movie['links'][0]['title'], title)
        resolvable = 'resolvable' in movie['links'][0] and movie['links'][0]['resolvable'] or True
        return play_video(path=movie['links'][0]['link'], resolvable=resolvable, title=title, thumb=thumb)

    print("***********************Found Total Link %d" % len(movie['links']))
    xbmcplugin.setPluginCategory(HANDLE, title)
    xbmcplugin.setContent(HANDLE, 'movies')
    for item in movie['links']:
        list_item = xbmcgui.ListItem(label=item['title'])
        list_item.setIconImage('DefaultVideo.png')
        list_item.setArt({'thumb': thumb})
        title = "%s - %s" % (item['title'], title)
        resolvable = 'resolvable' in item and item['resolvable'] or True
        url = build_url({'mode': 'play', 'url': item['link'], 'title': title,
                         'thumb': thumb, 'resolvable': resolvable,
                         'module': module, 'class': classname})
        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, False)

    xbmcplugin.endOfDirectory(HANDLE)


def play_video(path, resolvable=True, title=None, thumb=None):
    # dialog = xbmcgui.Dialog()
    # duration = 5000  # in milliseconds
    play_item = xbmcgui.ListItem(path=path)
    play_item.setLabel(title)
    play_item.setArt({'thumb': thumb})
    stream_url = None
    if resolvable:
        import urlresolver
        stream_url = urlresolver.HostedMediaFile(url=path).resolve()

    if not stream_url:
        print("*********************** Play stream %s " % path)
        xbmc.Player().play(path, play_item)
    else:
        print("*********************** Play stream %s " % stream_url)
        play_item.setPath(stream_url)
        # dialog.notification("URL Resolver", "Playing video", xbmcgui.NOTIFICATION_INFO, duration)
        xbmc.Player().play(stream_url, play_item)

    # xbmcplugin.setResolvedUrl(HANDLE, True, listitem=play_item)


def dosearch(plugin, module, classname, text, page=1):
    xbmcplugin.setPluginCategory(HANDLE, 'Search Result')
    xbmcplugin.setContent(HANDLE, 'movies')
    if text is None:
        keyboard = xbmc.Keyboard('', 'Search iPlayer')
        keyboard.doModal()
        if keyboard.isConfirmed():
            text = keyboard.getText()

    print("*********************** searching %s" % text)
    movies = plugin().search(text)

    if movies is not None:
        for item in movies['movies']:
            try:
                list_item = xbmcgui.ListItem(label=item['label'])
                list_item.setLabel2(item['realtitle'])
                list_item.setIconImage('DefaultVideo.png')
                list_item.setArt({
                    'thumb': item['thumb'],
                })
                url = build_url(
                    {'mode': 'movie', 'url': item['id'], 'thumb': item['thumb'], 'title': item['title'],
                     'module': module, 'class': classname})
                is_folder = True
                xbmcplugin.addDirectoryItem(HANDLE, url, list_item, is_folder)
            except:
                print(item)
    else:
        return
    xbmcplugin.endOfDirectory(HANDLE)


def search(module, classname):
    xbmcplugin.setPluginCategory(HANDLE, 'Search')
    xbmcplugin.setContent(HANDLE, 'movies')
    url = build_url({'mode': 'dosearch', 'module': module, 'class': classname})
    xbmcplugin.addDirectoryItem(HANDLE,
                                url,
                                xbmcgui.ListItem(label="[COLOR orange][B]%s[/B][/COLOR]" % "Enter search text ..."),
                                True)

    # Support to save search history

    xbmcplugin.endOfDirectory(HANDLE)


def get_plugin(arg):
    classname = ARGS.get('class', None)[0]
    module = ARGS.get('module', None)[0]
    print("*********************** Run module: %s - plugin: %s " % (module, classname))
    return getattr(import_module(module), classname), module, classname


def router():
    mode = ARGS.get('mode', None)
    instance = module = classname = None
    if mode is not None:
        instance, module, classname = get_plugin(ARGS)

    if mode is None:
        onInit()

    elif mode[0] == 'category':
        if 'subcategory' in ARGS:
            list_category(json.loads(ARGS.get('subcategory')[0]), module, classname)
        else:
            list_category(instance().getCategory(), module, classname)

    elif mode[0] == 'movies':
        link = ARGS.get('url')[0]
        page = int(ARGS.get('page')[0])
        print("*********************** Display %s page %s" % (link, page))
        movies = instance().getChannel(link, page)
        list_movie(movies, link, page, module, classname)

    elif mode[0] == 'movie':
        id = ARGS.get('url')[0]
        thumb = ARGS.get('thumb')[0]
        title = ARGS.get('title')[0]
        movie = instance().getMovie(id)
        print("*********************** Display movie %s %s" % (title, id))
        if len(movie['episode']) > 0 or len(movie['group']) > 0:
            show_episode(movie, thumb, title, module, classname)
        else:
            show_links(movie, title, thumb, module, classname)

    elif mode[0] == 'links':
        url = ARGS.get('url')[0]
        title = ARGS.get('title')[0]
        thumb = ARGS.get('thumb')[0]
        print("*********************** Get Movie Link %s" % url)
        movie = instance().getLink(url)
        show_links(movie, title, thumb, module, classname)

    elif mode[0] == 'play':
        path = ARGS.get('url')[0]
        title = ARGS.get('title')[0]
        thumb = ARGS.get('thumb')[0]
        resolvable = ARGS.get('resolvable')[0]
        play_video(path, resolvable, title, thumb)

    elif mode[0] == 'search':
        search(module, classname)

    elif mode[0] == 'dosearch':
        text = ARGS.get('url') and ARGS.get('url')[0] or None
        dosearch(instance, module, classname, text)