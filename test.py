import google.generativeai as genai
genai.configure(api_key="AIzaSyCBrSn46GVynMxTMX_iG_1M0qPibOzFHy0")
model = genai.GenerativeModel("gemini-1.5-flash")
print(model.generate_content("Hello Gemini!").text)
