# lambda/index.py
import json
import os
import urllib.request
import urllib.error
import re  # 正規表現モジュールをインポート
# from botocore.exceptions import ClientError

# FastAPIのエンドポイントURL
FASTAPI_URL = os.environ.get("FASTAPI_URL", "https://6265-34-87-2-35.ngrok-free.app")

def lambda_handler(event, context):
    try:

        print("Received event:", json.dumps(event))

        # Cognitoで認証されたユーザー情報を取得
        user_info = None
        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            user_info = event['requestContext']['authorizer']['claims']
            print(f"Authenticated user: {user_info.get('email') or user_info.get('cognito:username')}")

        # リクエストボディの解析
        body = json.loads(event['body'])
        message = body['message']
        conversation_history = body.get('conversationHistory', [])

        print("Processing message:", message)

        # 会話履歴を使用
        messages = conversation_history.copy()

        # ユーザーメッセージを追加
        messages.append({
            "role": "user",
            "content": message
        })

        # FastAPI用のリクエストペイロードを構築
        request_payload = {
            "messages": messages
        }
        print("Calling FastAPI with payload:", json.dumps(request_payload))

        # FastAPIエンドポイントにリクエストを送信（urllibで）
        headers = {
            "Content-Type": "application/json"
        }
        data = json.dumps(request_payload).encode("utf-8")
        req = urllib.request.Request(FASTAPI_URL, data=data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req) as res:
                response_body = res.read().decode("utf-8")
                response_data = json.loads(response_body)
        except urllib.error.HTTPError as e:
            raise Exception(f"FastAPI returned an error: {e.code}, {e.read().decode('utf-8')}")
        except urllib.error.URLError as e:
            raise Exception(f"Failed to reach FastAPI endpoint: {e.reason}")

        print("FastAPI response:", json.dumps(response_data, default=str))

        # アシスタントの応答を取得
        assistant_response = response_data.get('response')
        if not assistant_response:
            raise Exception("No response content from the FastAPI model")

        # アシスタントの応答を会話履歴に追加
        messages.append({
            "role": "assistant",
            "content": assistant_response
        })

        # 成功レスポンスの返却
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": True,
                "response": assistant_response,
                "conversationHistory": messages
            })
        }

    except Exception as error:
        print("Error:", str(error))

        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "error": str(error)
            })
        }
    