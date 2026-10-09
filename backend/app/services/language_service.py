"""
KRISHIRAKSHA AI - Multi-Language Service & DLT SMS Templates

Supports 11 Indian Languages:
English, Hindi, Telugu, Tamil, Kannada, Malayalam, Marathi, Bengali, Odia, Gujarati, Punjabi
"""

from typing import Dict, Any, Optional
from backend.app.config import settings

# Supported Indian languages registry
SUPPORTED_LANGUAGES = [
    "English",
    "Telugu",
    "Hindi",
    "Tamil",
    "Kannada",
    "Malayalam",
    "Marathi",
    "Bengali",
    "Odia",
    "Gujarati",
    "Punjabi"
]

# State-to-default-language mappings
STATE_DEFAULT_LANGUAGES = {
    "Andhra Pradesh": "Telugu",
    "Telangana": "Telugu",
    "Tamil Nadu": "Tamil",
    "Karnataka": "Kannada",
    "Kerala": "Malayalam",
    "Maharashtra": "Marathi",
    "West Bengal": "Bengali",
    "Odisha": "Odia",
    "Gujarat": "Gujarati",
    "Punjab": "Punjabi",
    "Bihar": "Hindi",
    "Uttar Pradesh": "Hindi",
    "Madhya Pradesh": "Hindi",
    "Rajasthan": "Hindi",
    "Haryana": "Hindi",
    "Assam": "English",
}

# DLT-approved template structures for Indian telecommunications
DLT_TEMPLATES = {
    "English": {
        "name": "KRISHI_WEATHER_ALERT_EN",
        "env_key": "MSG91_TEMPLATE_ID_EN",
        "pattern": (
            "WEATHER ALERT - KRISHIRAKSHA\n"
            "Location: {district}, {state}\n"
            "Heavy rainfall / high weather risk expected during {period}.\n"
            "Protect standing crops, harvested produce & farm equipment. Clear field drainage channels and follow official local advisories."
        )
    },
    "Telugu": {
        "name": "KRISHI_WEATHER_ALERT_TE",
        "env_key": "MSG91_TEMPLATE_ID_TE",
        "pattern": (
            "వాతావరణ హెచ్చరిక - కృషీరక్ష\n"
            "ప్రాంతం: {district}, {state}\n"
            "{period} సమయంలో భారీ వర్షాల ముప్పు ఉంది.\n"
            "పంటలు, కోసిన ఉత్పత్తులు మరియు వ్యవసాయ పరికరాలను సురక్షిత ప్రదేశంలో ఉంచండి. పొలాల్లో నీటి పారుదల మార్గాలను పరిశీలించండి. అధికారిక సూచనలను పాటించండి."
        )
    },
    "Hindi": {
        "name": "KRISHI_WEATHER_ALERT_HI",
        "env_key": "MSG91_TEMPLATE_ID_HI",
        "pattern": (
            "मौसम चेतावनी - कृषिरक्षा\n"
            "स्थान: {district}, {state}\n"
            "{period} के दौरान भारी वर्षा और मौसम जोखिम की संभावना है।\n"
            "कृपया फसलों, कटी हुई उपज और कृषि उपकरणों को सुरक्षित स्थान पर रखें। खेतों में जल निकासी की व्यवस्था करें और स्थानीय प्रशासनिक दिशा-निर्देशों का पालन करें।"
        )
    },
    "Tamil": {
        "name": "KRISHI_WEATHER_ALERT_TA",
        "env_key": "MSG91_TEMPLATE_ID_TA",
        "pattern": (
            "வானிலை எச்சரிக்கை - கிருஷிரக்ஷா\n"
            "இடம்: {district}, {state}\n"
            "{period} காலத்தில் மிக பலத்த மழை மற்றும் வெள்ள அபாயம் எதிர்பார்க்கப்படுகிறது.\n"
            "பயிர்கள், அறுவடை செய்த விளைபொருட்கள் மற்றும் விவசாய கருவிகளை பாதுகாப்பான இடத்திற்கு மாற்றவும். வடிகால் வாய்க்கால்களை சீரமைக்கவும்."
        )
    },
    "Kannada": {
        "name": "KRISHI_WEATHER_ALERT_KN",
        "env_key": "MSG91_TEMPLATE_ID_KN",
        "pattern": (
            "ಹವಾಮಾನ ಎಚ್ಚರಿಕೆ - ಕೃಷಿರಕ್ಷಾ\n"
            "ಸ್ಥಳ: {district}, {state}\n"
            "{period} ಅವಧಿಯಲ್ಲಿ ಭಾರಿ ಮಳೆಯಾಗುವ ಸಾಧ್ಯತೆಯಿದೆ.\n"
            "ಬೆಳೆಗಳು, ಕೊಯ್ಲು ಮಾಡಿದ ಧಾನ್ಯ ಮತ್ತು ಕೃಷಿ ಉಪಕರಣಗಳನ್ನು ಸುರಕ್ಷಿತ ಸ್ಥಳದಲ್ಲಿ ಇರಿಸಿ. ಹೊಲಗಳಲ್ಲಿ ನೀರು ಸರಾಗವಾಗಿ ಹರಿಯಲು ಕಾಲುವೆಗಳನ್ನು ತೆರವುಗೊಳಿಸಿ."
        )
    },
    "Malayalam": {
        "name": "KRISHI_WEATHER_ALERT_ML",
        "env_key": "MSG91_TEMPLATE_ID_ML",
        "pattern": (
            "കാലാവസ്ഥാ മുന്നറിയിപ്പ് - കൃഷിരക്ഷ\n"
            "സ്ഥലം: {district}, {state}\n"
            "{period} സമയത്ത് അതിതീവ്ര മഴയ്ക്ക് സാധ്യതയുണ്ട്.\n"
            "വിളകളും കാർഷിക ഉപകരണങ്ങളും സുരക്ഷിത സ്ഥാനത്തേക്ക് മാറ്റുക. കൃഷിയിടങ്ങളിലെ നീരൊഴുക്ക് ഉറപ്പാക്കുക. ഔദ്യോഗിക നിർദ്ദേശങ്ങൾ പാലിക്കുക."
        )
    },
    "Marathi": {
        "name": "KRISHI_WEATHER_ALERT_MR",
        "env_key": "MSG91_TEMPLATE_ID_MR",
        "pattern": (
            "हवामान इशारा - कृषीरक्षा\n"
            "ठिकाण: {district}, {state}\n"
            "{period} दरम्यान मुसळधार पाऊस व पुराचा धोका संभवतो.\n"
            "उभी पिके, काढणी केलेले धान्य व कृषी अवजारे सुरक्षित स्थळी ठेवावीत. शेतातील पाण्याचा निचरा मोकळा करावा."
        )
    },
    "Bengali": {
        "name": "KRISHI_WEATHER_ALERT_BN",
        "env_key": "MSG91_TEMPLATE_ID_BN",
        "pattern": (
            "আবহাওয়া সতর্কতা - কৃষিরক্ষা\n"
            "স্থান: {district}, {state}\n"
            "{period} সময়ে ভারী বৃষ্টির পূর্বাভাস রয়েছে।\n"
            "ফসল, কাটা শস্য এবং কৃষি সরঞ্জাম নিরাপদ স্থানে রাখুন। জমিতে জল নিষ্কাশনের ব্যবস্থা করুন এবং সরকারি নির্দেশ মান্য করুন।"
        )
    },
    "Odia": {
        "name": "KRISHI_WEATHER_ALERT_OR",
        "env_key": "MSG91_TEMPLATE_ID_OR",
        "pattern": (
            "ପାଣିପାଗ ସତର୍କତା - କୃଷିରକ୍ଷା\n"
            "ସ୍ଥାନ: {district}, {state}\n"
            "{period} ମଧ୍ୟରେ ପ୍ରବଳ ବର୍ଷା ସମ୍ଭାବନା ଅଛି।\n"
            "ଫସଲ ଓ କୃଷି ଉପକରଣକୁ ସୁରକ୍ଷିତ ସ୍ଥାନରେ ରଖନ୍ତୁ। ଜମିରୁ ଜଳ ନିଷ୍କାସନ ବ୍ୟବସ୍ଥା କରନ୍ତୁ।"
        )
    },
    "Gujarati": {
        "name": "KRISHI_WEATHER_ALERT_GU",
        "env_key": "MSG91_TEMPLATE_ID_GU",
        "pattern": (
            "હવામાન ચેતવણી - કૃષિરક્ષા\n"
            "સ્થળ: {district}, {state}\n"
            "{period} દરમિયાન ભારે વરસાદની સંભાવના છે.\n"
            "પાક, કાપણી કરેલ અનાજ અને સાધનો સલામત સ્થળે રાખો. ખેતરમાંથી પાણીના નિકાલની વ્યવસ્થા કરો."
        )
    },
    "Punjabi": {
        "name": "KRISHI_WEATHER_ALERT_PA",
        "env_key": "MSG91_TEMPLATE_ID_PA",
        "pattern": (
            "ਮੌਸਮ ਚੇਤਾਵਨੀ - ਕ੍ਰਿਸ਼ੀਰਕਸ਼ਾ\n"
            "ਸਥਾਨ: {district}, {state}\n"
            "{period} ਦੌਰਾਨ ਭਾਰੀ ਮੀਂਹ ਦਾ ਖਤਰਾ ਹੈ।\n"
            "ਕਿਰਪਾ ਕਰਕੇ ਫਸਲਾਂ, ਕੱਟੀ ਹੋਈ ਉਪਜ ਅਤੇ ਖੇਤੀਬਾੜੀ ਦੇ ਸੰਦਾਂ ਨੂੰ ਸੁਰੱਖਿਅਤ ਥਾਂ 'ਤੇ ਰੱਖੋ ਅਤੇ ਖੇਤਾਂ 'ਚੋਂ ਪਾਣੀ ਦੇ ਨਿਕਾਸ ਦਾ ਪ੍ਰਬੰਧ ਕਰੋ।"
        )
    }
}

class LanguageService:
    @staticmethod
    def get_supported_languages():
        return SUPPORTED_LANGUAGES

    @staticmethod
    def resolve_language(farmer_preferred: Optional[str], state_name: Optional[str]) -> str:
        """
        Resolves language hierarchy:
        1. Farmer's explicitly chosen preferred_language
        2. Configured default language for the farmer's state
        3. English as universal fallback
        """
        if farmer_preferred and farmer_preferred in SUPPORTED_LANGUAGES:
            return farmer_preferred
        if state_name and state_name in STATE_DEFAULT_LANGUAGES:
            return STATE_DEFAULT_LANGUAGES[state_name]
        return "English"

    @staticmethod
    def get_template_id(language: str) -> Optional[str]:
        """
        Returns the DLT template ID configured for this language from environment variables.
        """
        mapping = {
            "English": settings.MSG91_TEMPLATE_ID_EN,
            "Telugu": settings.MSG91_TEMPLATE_ID_TE,
            "Hindi": settings.MSG91_TEMPLATE_ID_HI,
            "Tamil": settings.MSG91_TEMPLATE_ID_TA,
            "Kannada": settings.MSG91_TEMPLATE_ID_KN,
            "Malayalam": settings.MSG91_TEMPLATE_ID_ML,
            "Marathi": settings.MSG91_TEMPLATE_ID_MR,
            "Bengali": settings.MSG91_TEMPLATE_ID_BN,
            "Odia": settings.MSG91_TEMPLATE_ID_OR,
            "Gujarati": settings.MSG91_TEMPLATE_ID_GU,
            "Punjabi": settings.MSG91_TEMPLATE_ID_PA,
        }
        return mapping.get(language)

    @staticmethod
    def render_sms_content(language: str, district: str = "", state: str = "", period: str = "Next 24-48 Hours", **kwargs) -> str:
        """
        Fills the approved DLT template pattern with validated variables.
        """
        dist = district or kwargs.get("district_name", "")
        st = state or kwargs.get("state_name", "")
        p = period or kwargs.get("period", "Next 24-48 Hours")
        lang = language if language in DLT_TEMPLATES else "English"
        pattern = DLT_TEMPLATES[lang]["pattern"]
        return pattern.format(district=dist, state=st, period=p)

    @staticmethod
    def get_all_templates_status() -> Dict[str, Dict[str, Any]]:
        """
        Audits configured DLT template IDs per language.
        """
        res = {}
        for lang, info in DLT_TEMPLATES.items():
            tmpl_id = LanguageService.get_template_id(lang)
            res[lang] = {
                "template_name": info["name"],
                "dlt_template_id": tmpl_id,
                "is_configured": bool(tmpl_id and len(tmpl_id.strip()) > 0),
                "sample_preview": LanguageService.render_sms_content(lang, "District", "State")
            }
        return res

language_service = LanguageService()
