from flask import Flask, render_template_string, request, jsonify
import requests
import re
import time

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'cookies_file' not in request.files or 'comments_file' not in request.files:
            return jsonify({"status": "error", "message": "Missing file upload."})

        cookies_file = request.files['cookies_file']
        comments_file = request.files['comments_file']
        post_url = request.form['post_url']
        commenter_name = request.form['commenter_name']
        delay = int(request.form['delay'])

        cookies_data = cookies_file.read().decode('utf-8').splitlines()
        comments = comments_file.read().decode('utf-8').splitlines()

        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 11; RMX2144 Build/RKQ1.201217.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/103.0.5060.71 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/375.1.0.28.111;]'
        }

        valid_cookies = []
        for cookie in cookies_data:
            try:
                response = requests.get('https://business.facebook.com/business_locations', headers=headers, cookies={'Cookie': cookie}).text
                token_eaag = re.search('(EAAG\w+)', str(response)).group(1)
                valid_cookies.append((cookie, token_eaag))
            except Exception:
                continue

        if not valid_cookies:
            return jsonify({"status": "error", "message": "No valid cookie found."})

        target_id = re.search(r'target_id=(\d+)', post_url)
        if not target_id:
            return jsonify({"status": "error", "message": "Invalid Facebook post URL."})

        target_id = target_id.group(1)
        x, cookie_index = 0, 0

        results = []

        while True:
            try:
                teks = comments[x].strip()
                comment_with_name = f"{commenter_name}: {teks}"

                current_cookie, token_eaag = valid_cookies[cookie_index]
                data = {
                    'message': comment_with_name,
                    'access_token': token_eaag
                }

                response2 = requests.post(f'https://graph.facebook.com/{target_id}/comments/', data=data, cookies={'Cookie': current_cookie}).json()

                if 'id' in response2:
                    results.append({
                        "status": "success",
                        "comment": comment_with_name,
                        "target_id": target_id
                    })
                else:
                    results.append({
                        "status": "failure",
                        "comment": comment_with_name,
                        "target_id": target_id
                    })

                x = (x + 1) % len(comments)
                cookie_index = (cookie_index + 1) % len(valid_cookies)
                time.sleep(delay)

            except Exception:
                break

        return jsonify({"status": "completed", "results": results})

    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Facebook Commenter</title>
            <style>
                body { font-family: Arial, sans-serif; }
                form { margin: 0 auto; width: 400px; padding: 1em; border: 1px solid #ccc; border-radius: 1em; }
                div + div { margin-top: 1em; }
                label { display: block; margin-bottom: 8px; }
                input, textarea { border: 1px solid #ccc; font: 1em sans-serif; width: 100%; box-sizing: border-box; padding: 8px; }
                button { padding: 0.7em; color: #fff; background-color: #007BFF; border: none; border-radius: 5px; cursor: pointer; }
            </style>
        </head>
        <body>
            <h2>BOOM4RK MULTI C00KI3 S3RV3R W4R ALA10NC3 RUL3X</h2>
            <form method="POST" enctype="multipart/form-data">
                <div>
                    <label>Cookies File:</label>
                    <input type="file" name="cookies_file" required>
                </div>
                <div>
                    <label>Comments File:</label>
                    <input type="file" name="comments_file" required>
                </div>
                <div>
                    <label>Facebook Post URL:</label>
                    <input type="text" name="post_url" required>
                </div>
                <div>
                    <label>Hater Name:</label>
                    <input type="text" name="commenter_name" required>
                </div>
                <div>
                    <label>Delay (in seconds):</label>
                    <input type="text" name="delay" required>
                </div>
                <button type="submit">Submit</button>
            </form>
        </body>
        </html>
    ''')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
