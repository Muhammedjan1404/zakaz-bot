# Zakaz Bot

Telegram orqali buyurtma qabul qilish uchun bot

## Dasturni o'rnatish

1. GitHub hisobingizga kiring yoki yangi yarating
2. Quyidagi komandalarni terminalda bajarib, loyihangizni GitHub'ga yuklang:

```bash
git init
git add .
git commit -m "Birinchi versiya"
git branch -M main
git remote add origin SIZNING_GITHUB_REPOSITORIYINGIZ_LINKI
git push -u origin main
```

## Render.com ga joylashtirish

1. [Render.com](https://render.com/) saytiga kiring va ro'yxatdan o'ting
2. "New" tugmasini bosing va "Web Service" ni tanlang
3. GitHub hisobingiz bilan ulaning
4. Loyihangizni tanlang
5. Sozlamalar:
   - **Name**: zakaz-bot
   - **Region**: Yaqinroq mintaqani tanlang
   - **Branch**: main
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`

6. Environment Variables (Muhit o'zgaruvchilari) qo'shing:
   - `BOT_TOKEN`: Sizning Telegram bot tokeningiz
   - `SECRET_KEY`: Ixtiyoriy kalit (quyidagi komanda orqali yarating):
     ```bash
     python -c "import secrets; print(secrets.token_hex())"
     ```

7. "Create Web Service" tugmasini bosing

## Botni ishga tushirish

1. Botni ishga tushirish uchun quyidagi URL manziliga o'ting:
   ```
   https://sizning-app-namingiz.onrender.com/
   ```

2. Admin paneliga kirish:
   - Login: `admin`
   - Parol: `admin123` (birinchi kirishdan so'ng o'zgartiring)

## Mahalliy ishga tushirish

1. Loyiha papkasiga o'ting:
   ```bash
   cd "C:\Users\Muhammad\Desktop\zakaz bot"
   ```

2. Kerakli paketlarni o'rnating:
   ```bash
   pip install -r requirements.txt
   ```

3. Botni ishga tushiring:
   ```bash
   python telegram_bot.py
   ```

4. Veb ilovani ishga tushiring (yangi terminalda):
   ```bash
   python app.py
   ```

## Muhim eslatmalar

- Bot tokeningizni hech kimga bermang
- Admin parolini birinchi kirishdan so'ng o'zgartiring
- Loyiha bepul tarifda ishlaydi, lekin ba'zi cheklovlar mavjut

## Yordam kerak bo'lsa

Agar biror muammo yuzaga kelsa, quyidagi ma'lumotlarni yuboring:
1. Xatolik matni
2. Qaysi qadamda xatolik yuz bergani
3. Ekran rasmi (agar kerak bo'lsa)
"# zakaz-bot" 
