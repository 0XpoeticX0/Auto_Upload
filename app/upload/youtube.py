import os
from app.logger import logger
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def get_authenticated_service():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('client_secrets.json'):
                logger.error("client_secrets.json missing. Cannot authenticate YouTube.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secrets.json', SCOPES)
            creds = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
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
        # Map category to YouTube category ID
        CATEGORY_IDS = {
            "educational": "27",    # Education
            "crime_thriller": "25", # News & Politics
            "knowledge": "27",      # Education
            "funny": "23",          # Comedy
            "motivational": "22",   # People & Blogs
        }
        video_category = metadata.get("category", "educational")
        category_id = CATEGORY_IDS.get(video_category, "27")

        body = {
            'snippet': {
                'title': metadata.get('youtube_title', 'Generated Short')[:100],
                'description': metadata.get('description', ''),
                'tags': metadata.get('tags', []),
                'categoryId': category_id
            },
            'status': {
                'privacyStatus': 'public',
                'selfDeclaredMadeForKids': False
            }
        }
        
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
        logger.info(f"YouTube Video uploaded successfully! Video ID: {video_id}")
        
        # Upload Thumbnail if provided
        if thumbnail_path and os.path.exists(thumbnail_path):
            logger.info("Uploading custom thumbnail to YouTube...")
            try:
                youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(thumbnail_path)
                ).execute()
                logger.info("Custom thumbnail uploaded successfully.")
            except HttpError as e:
                logger.warning(f"Could not upload thumbnail (Account might not be phone-verified for custom thumbnails): {e}")
            except Exception as e:
                logger.error(f"Failed to upload thumbnail: {e}")
                
        # Upload Captions (VTT) if provided
        if vtt_path and os.path.exists(vtt_path):
            logger.info("Uploading subtitle/caption track to YouTube for maximum SEO reach...")
            try:
                youtube.captions().insert(
                    part="snippet",
                    body={
                        "snippet": {
                            "videoId": video_id,
                            "language": "en",
                            "name": "English",
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
                
        return True
        
    except HttpError as e:
        logger.error(f"An HTTP error {e.resp.status} occurred during YouTube upload: {e.content}")
        return False
    except Exception as e:
        logger.error(f"Error uploading to YouTube: {e}")
        return False
