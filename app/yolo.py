import os
import logging
import requests

logger = logging.getLogger(__name__)

# Endpoint configuration: this should be your HuggingFace Space base URL
# Example: set YOLO_API_URL=https://amashtce-food-yolo-api.hf.space
YOLO_API_URL = os.environ.get('YOLO_API_URL', 'https://amashtce-food-yolo-api.hf.space')
YOLO_API_TIMEOUT = int(os.environ.get('YOLO_API_TIMEOUT', '30'))
YOLO_API_MAX_RETRIES = int(os.environ.get('YOLO_API_MAX_RETRIES', '3'))


class YOLOApiError(Exception):
    pass


def _build_predict_url(base_url: str) -> str:
    # ensure we call the /predict path
    if base_url.endswith('/predict') or base_url.endswith('/predict/'):
        return base_url
    return base_url.rstrip('/') + '/predict'


def predict_foods(image_path):
    """
    POST the image file to the remote YOLO API (field name `file`) and return the
    list of detected food names (list). On error raises YOLOApiError or returns []
    if parsing fails.
    """
    url = _build_predict_url(YOLO_API_URL)
    try:
        with open(image_path, 'rb') as fh:
            files = {'file': (os.path.basename(image_path), fh, 'application/octet-stream')}
            # Retry loop for transient network issues
            last_exc = None
            for attempt in range(1, YOLO_API_MAX_RETRIES+1):
                try:
                    resp = requests.post(url, files=files, timeout=YOLO_API_TIMEOUT)
                    if resp.status_code != 200:
                        raise YOLOApiError(f'YOLO API returned status {resp.status_code}: {resp.text[:500]}')
                    data = resp.json()
                    break
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                    logger.warning('YOLO API request attempt %s failed: %s', attempt, e)
                    last_exc = e
                    if attempt < YOLO_API_MAX_RETRIES:
                        import time
                        time.sleep(2 ** (attempt-1))
                        continue
                    raise YOLOApiError(f'YOLO API request failed after {YOLO_API_MAX_RETRIES} attempts: {e}')
                except ValueError as e:
                    # JSON parse error
                    raise YOLOApiError('YOLO API returned invalid JSON')
            foods = data.get('foods', []) if isinstance(data, dict) else []
            if not isinstance(foods, list):
                raise YOLOApiError('YOLO API returned invalid payload')

            # normalize and deduplicate while preserving order
            seen = set()
            out = []
            for f in foods:
                s = str(f).strip()
                if not s or s in seen:
                    continue
                seen.add(s)
                out.append(s)
            return out

    except requests.exceptions.RequestException as e:
        logger.warning('YOLO API request failed: %s', e)
        raise YOLOApiError(f'YOLO API request failed: {e}')
    except YOLOApiError:
        raise
    except Exception as e:
        logger.exception('Unexpected error calling YOLO API: %s', e)
        raise YOLOApiError('Unexpected error while calling YOLO API')
