from deep_translator import GoogleTranslator

text = "Easter eggs and References: On the back of the book there is a QR code leading to BakeeZy's Youtube channel"
translated = GoogleTranslator(source='auto', target='zh-CN').translate(text)
print(translated)
