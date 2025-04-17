from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    FlexSendMessage, BubbleContainer, BoxComponent, TextComponent
)
import os

app = Flask(__name__)

# ตั้งค่าจาก LINE Developer Console (TB Bot)
LINE_CHANNEL_ACCESS_TOKEN = "Ydm+eCQfog7k4nHLe7MqXCzaE8GUki4ycKsAcQb9099Pllb9XASENVi1kFUIJO0kXN5qsdPq9/lts/mYMn3JC7D9066dleLszkiTuWWTaXui6fJvkFKLz3hm0KfreALtNBSc8xwQyyp/DyPemexzJAdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "363d1196a1fdeeebeb38866b6dca17f5"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

def build_tb_flex(weight):
    # กลุ่มน้ำหนัก
    if weight < 35:
        weight_range = "น้ำหนักต่ำกว่าเกณฑ์ (<35 กก.)"
        recommended = {"H": "-", "R": "-", "Z": "-", "E": "-"}
    elif 35 <= weight <= 49:
        weight_range = "35-49 กก."
        recommended = {"H": 300, "R": 450, "Z": 1000, "E": 800}
    elif 50 <= weight <= 69:
        weight_range = "50-69 กก."
        recommended = {"H": 300, "R": 600, "Z": 1500, "E": 1000}
    else:
        weight_range = ">70 กก."
        recommended = {"H": 300, "R": 600, "Z": 2000, "E": 1200}

    # คำนวณ min-max ตามสูตร
    h_min = round(4 * weight)
    h_max = round(6 * weight)
    r_min = round(8 * weight)
    r_max = round(12 * weight)
    z_min = round(20 * weight)
    z_max = round(30 * weight)
    e_min = round(15 * weight)
    e_max = round(20 * weight)

    bubble = BubbleContainer(
        body=BoxComponent(
            layout="vertical",
            contents=[
                TextComponent(text=f"TB ยาตามน้ำหนัก", weight="bold", size="lg"),
                TextComponent(text=f"น้ำหนัก: {weight} กก.", margin="md"),
                TextComponent(text=f"กลุ่มน้ำหนักแนะนำ: {weight_range}", margin="sm", size="sm", color="#555555"),
                BoxComponent(
                    layout="vertical",
                    margin="lg",
                    spacing="sm",
                    contents=[
                        TextComponent(text="➖ ขนาดยาคำนวณได้:", weight="bold", size="md", margin="md"),
                        TextComponent(text=f"H (Isoniazid): {h_min}-{h_max} มก./วัน", size="sm"),
                        TextComponent(text=f"R (Rifampicin): {r_min}-{r_max} มก./วัน", size="sm"),
                        TextComponent(text=f"Z (Pyrazinamide): {z_min}-{z_max} มก./วัน", size="sm"),
                        TextComponent(text=f"E (Ethambutol): {e_min}-{e_max} มก./วัน", size="sm"),
                        TextComponent(text="➖ ขนาดยาที่แนะนำ:", weight="bold", size="md", margin="lg"),
                        TextComponent(text=f"H: {recommended['H']} มก./วัน", size="sm"),
                        TextComponent(text=f"R: {recommended['R']} มก./วัน", size="sm"),
                        TextComponent(text=f"Z: {recommended['Z']} มก./วัน", size="sm"),
                        TextComponent(text=f"E: {recommended['E']} มก./วัน", size="sm"),
                    ]
                )
            ]
        )
    )
    return FlexSendMessage(alt_text="ผลคำนวณยาวัณโรค", contents=bubble)


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip()
    try:
        weight = float(text)
        if 20 <= weight <= 200:
            flex_msg = build_tb_flex(weight)
            line_bot_api.reply_message(event.reply_token, flex_msg)
            return
        else:
            reply = "กรุณากรอกน้ำหนักที่อยู่ในช่วง 20-200 กก."
    except ValueError:
        reply = "กรุณากรอกน้ำหนักเป็นตัวเลข เช่น 52"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

@app.route("/", methods=["GET"])
def index():
    return "TB Bot is running!"

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
