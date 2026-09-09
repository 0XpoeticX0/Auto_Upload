import os
from app.logger import logger
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.force-ssl',
    'https://www.googleapis.com/auth/youtube'
]

def get_authenticated_service():
    creds = None
    if os.path.exists('token.json'):
        try:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        except Exception as e:
            logger.warning(f"Could not load token.json: {e}")
            creds = None
        
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                logger.info("Attempting to refresh YouTube access token...")
                creds.refresh(Request())
                logger.info("Successfully refreshed YouTube token!")
            except Exception as e:
                logger.warning(f"Failed to refresh YouTube credentials (expired or revoked): {e}")
                if os.path.exists('token.json'):
                    try:
                        os.remove('token.json')
                        logger.info("Removed stale token.json")
                    except Exception:
                        pass
                creds = None

        if not creds:
            if not os.path.exists('client_secrets.json'):
                logger.error("client_secrets.json missing. Cannot authenticate YouTube.")
                return None
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'client_secrets.json',
                    SCOPES,
                    redirect_uri='http://localhost:8080/'
                )
                auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
                print("\n" + "=" * 70)
                print("[!] YOUTUBE GOOGLE OAUTH AUTHORIZATION REQUIRED")
                print(">> Please open or click this URL to log in with your YouTube Google account:")
                print(f"{auth_url}")
                print("=" * 70 + "\n", flush=True)

                creds = flow.run_local_server(
                    host='localhost',
                    port=8080,
                    open_browser=True,
                    prompt='consent',
                    access_type='offline'
                )
            except Exception as e:
                logger.error(f"OAuth flow failed: {e}")
                return None
            
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            
    return build('youtube', 'v3', credentials=creds)

def upload_to_youtube(video_path: str, metadata: dict, thumbnail_path: str = None, vtt_path: str = None):
    logger.info(f"Starting YouTube Upload for {video_path}")
    
    if not os.path.exists("client_secrets.json") and not os.path.exists("token.json"):
        logger.warning("YouTube Upload Skipped: 'client_secrets.json' not found. Please download OAuth credentials from Google Cloud Console.")
        return False

    youtube = get_authenticated_service()
    if not youtube:
        return False
        
    try:
        # Category ID: Education (27)
        CATEGORY_IDS = {
            "educational": "27",
            "crime_thriller": "25",
            "knowledge": "27",
            "funny": "23",
            "motivational": "22",
        }
        video_category = metadata.get("category", "educational")
        category_id = CATEGORY_IDS.get(video_category, "27")

        body = {
            'snippet': {
                'title': metadata.get('youtube_title', 'Generated Short')[:100],
                'description': metadata.get('description', ''),
                'tags': metadata.get('tags', []),
                'categoryId': category_id,
                'defaultLanguage': 'bn',
                'defaultAudioLanguage': 'bn'
            },
            'status': {
                'privacyStatus': 'public',
                'selfDeclaredMadeForKids': False,
                'embeddable': True,
                'publicStatsViewable': True,
                'license': 'youtube'
            }
        }
        
        # Multi-Language Localizations (Global English Search Reach)
        en_title = metadata.get("english_title")
        en_desc = metadata.get("english_description")
        if en_title and en_desc:
            body['localizations'] = {
                'en': {
                    'title': en_title[:100],
                    'description': en_desc[:5000]
                }
            }
            body['snippet']['defaultLanguage'] = 'bn'
        
        media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype='video/mp4')
        
        request = youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=media
        )
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logger.info(f"YouTube Upload Progress: {int(status.progress() * 100)}%")
                
        video_id = response.get('id')
        logger.info(f"🎉 YouTube Video uploaded successfully! Video ID: {video_id} (https://youtube.com/shorts/{video_id})")
        
        # 1. Upload Custom Thumbnail if provided
        if thumbnail_path and os.path.exists(thumbnail_path):
            logger.info("Uploading custom thumbnail to YouTube...")
            try:
                youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(thumbnail_path)
                ).execute()
                logger.info("Custom thumbnail uploaded successfully.")
            except HttpError as e:
                logger.warning(f"Could not upload thumbnail: {e}")
            except Exception as e:
                logger.error(f"Failed to upload thumbnail: {e}")
                
        # 2. Upload Captions (VTT) if provided
        if vtt_path and os.path.exists(vtt_path):
            logger.info("Uploading subtitle/caption track to YouTube for maximum SEO reach...")
            try:
                youtube.captions().insert(
                    part="snippet",
                    body={
                        "snippet": {
                            "videoId": video_id,
                            "language": "bn",
                            "name": "Bangla",
                            "isDraft": False
                        }
                    },
                    media_body=MediaFileUpload(vtt_path, mimetype="text/vtt")
                ).execute()
                logger.info("Caption track uploaded successfully.")
            except HttpError as e:
                logger.warning(f"Could not upload captions: {e}")
            except Exception as e:
                logger.error(f"Failed to upload captions: {e}")
                
        # 3. Auto-Post Pinned First Comment for Instant Algorithm Boost
        comment_text = metadata.get("pinned_comment")
        if not comment_text:
            if "কুইজ" in metadata.get("youtube_title", "") or "quiz" in metadata.get("youtube_title", "").lower():
                comment_text = "আজকের কুইজে আপনার স্কোর ৫-এ কত হলো? ৫/৫, ৪/৫ নাকি ৩/৫? কমেন্টে জানান! 👇"
            else:
                comment_text = "সহীহ সুন্নাহর দাওয়াত ছড়িয়ে দিতে বন্ধুদের সাথে Share করুন—রাসূলুল্লাহ (ﷺ) বলেছেন: ‘যে ব্যক্তি কোনো ভালো কাজের পথ দেখায়, সে তার সমপরিমাণ সওয়াব পায়।’ [সহীহ মুসলিম: ১৮৯৩] 🌿"
                
        if comment_text and video_id:
            try:
                logger.info(f"Posting auto-first comment on YouTube video {video_id}...")
                youtube.commentThreads().insert(
                    part="snippet",
                    body={
                        "snippet": {
                            "videoId": video_id,
                            "topLevelComment": {
                                "snippet": {
                                    "textOriginal": comment_text
                                }
                            }
                        }
                    }
                ).execute()
                logger.info(f"✅ Auto-first comment posted on YouTube!")
            except Exception as e:
                logger.warning(f"Notice: Could not post first comment on YouTube: {e}")
                
        return True
        
    except HttpError as e:
        logger.error(f"An HTTP error {e.resp.status} occurred during YouTube upload: {e.content}")
        return False
    except Exception as e:
        logger.error(f"Error uploading to YouTube: {e}")
        return False
