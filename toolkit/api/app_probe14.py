#!/usr/bin/env python3
"""Second read-only column sweep for messages/admin_api_keys before the single approved INSERT."""
import ssl, json, time, http.cookiejar, urllib.request, urllib.error

CTX = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
BASE = "https://onlyfakeai.ru/api/supabase"
KEY = "<publishable-key>"
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPSHandler(context=CTX),
                                 urllib.request.HTTPCookieProcessor(cj))
TOK = json.load(open("their_token.txt"))["access_token"]
AUTH = {"apikey": KEY, "Authorization": "Bearer " + TOK}


def r(method, url, h=None, b=None):
    hh = {"User-Agent": UA}
    hh.update(h or {})
    rq = urllib.request.Request(url, data=b, headers=hh, method=method)
    try:
        with op.open(rq, timeout=20) as x:
            return x.status, dict(x.headers), x.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except Exception as e:
        return 0, {}, str(e).encode()


COLS = """message_content msg_content content_html message_html text_html body_html caption
description details note notes comment comments reply answer question prompt response image
image_path image_key media media_url media_type mime_type file_name filename file_path
storage_path photo photo_key thumb thumbnail thumb_url video_url document_url voice_url
audio_url chat_type update_id tg_update tg_data raw raw_data raw_update message_data
session_id conversation_id channel_id sender_user_id recipient_user_id is_deleted deleted
visible priority sequence seq sort admin_reply reply_text reply_image sent_by created_by
broadcast broadcast_id is_broadcast read_by opened_at clicked_at link link_url button
keyboard parse_mode entities first_name last_name language_code tg_user_id""".split()
for t, cols in [("messages", COLS), ("admin_api_keys", """api_key secret token plaintext
scopes scope permissions label description notes created_by last_used_at expires_at enabled""".split())]:
    found = []
    for c in cols:
        st, hd, b = r("GET", f"{BASE}/rest/v1/{t}?select={c}&limit=0", AUTH)
        if st == 200:
            found.append(c)
            print(f"  [{t}] EXISTS: {c}")
        time.sleep(0.09)
    print(f"== {t} extra columns: {found}")
