import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

export type Language = "en" | "hi" | "mr";

const LANG_KEY = "nyayasetu_language";

const translations = {
  en: {
    "nav.myCases": "My cases",
    "nav.newCase": "New case",
    "nav.logout": "Log out",
    "nav.login": "Log in",
    "nav.signup": "Sign up",
    "nav.tagline": "understand a risk before it becomes a case",

    "landing.eyebrow": "A preventive legal-risk tool for everyday situations",
    "landing.title": "Understand a legal risk before it becomes a court case.",
    "landing.subtitle":
      "Upload a notice or describe what happened. NyayaSetu explains what it found in plain language, flags deadlines, and points you to the right official service — with every claim linked to its source.",
    "landing.languageNote": "More languages can be added via Bhashini without changing this workflow.",
    "landing.emergency":
      "If you are in immediate physical danger, call 112. For a financial cyber fraud that just happened, call 1930 right away — don't wait to use this tool first.",
    "landing.beforeTitle": "Before you start",
    "landing.beforeBody":
      "Anything you upload or describe is used only to analyse your case. You can delete a case and its files at any time. This tool provides legal information, not legal advice — it will never decide who is right, predict what a court will do, or file anything for you.",
    "landing.whatHelp": "What would you like help with?",
    "domain.rental": "Rental & tenancy",
    "domain.rentalDesc": "A rent notice, eviction notice, or deposit dispute.",
    "domain.employment": "Employment",
    "domain.employmentDesc": "An offer letter, salary deduction, or termination notice.",
    "domain.consumer": "Consumer disputes",
    "domain.consumerDesc": "A faulty product, warranty issue, or service complaint.",
    "domain.cyber": "Cyber fraud",
    "domain.cyberDesc": "An online scam, UPI fraud, or account compromise.",

    "newcase.title": "Start a new case",
    "newcase.subtitle":
      "Choose what this is about, then upload a document, describe what happened, or record a short voice note.",
    "newcase.domainLabel": "What is this about?",
    "newcase.describe": "Describe it",
    "newcase.upload": "Upload a document",
    "newcase.voice": "Record voice note",
    "newcase.submit": "Analyse this case",

    "tab.overview": "What we found",
    "tab.facts": "Details we used",
    "tab.dates": "Important dates",
    "tab.action": "What to do next",
    "tab.evidence": "Evidence locker",
    "tab.draft": "Draft center",

    "footer.disclaimer":
      "NyayaSetu gives legal information and procedural guidance, not legal advice. It does not decide guilt, predict a court outcome, or submit anything on your behalf.",
  },
  hi: {
    "nav.myCases": "मेरे केस",
    "nav.newCase": "नया केस",
    "nav.logout": "लॉग आउट",
    "nav.login": "लॉग इन",
    "nav.signup": "साइन अप",
    "nav.tagline": "मामला बनने से पहले जोखिम को समझें",

    "landing.eyebrow": "रोज़मर्रा की स्थितियों के लिए एक निवारक कानूनी-जोखिम उपकरण",
    "landing.title": "कोर्ट केस बनने से पहले कानूनी जोखिम को समझें।",
    "landing.subtitle":
      "कोई नोटिस अपलोड करें या जो हुआ उसे बताएं। NyayaSetu सरल भाषा में समझाता है, ज़रूरी तारीखें बताता है, और सही सरकारी सेवा की ओर मार्गदर्शन करता है — हर जानकारी स्रोत के साथ।",
    "landing.languageNote": "Bhashini के ज़रिए और भाषाएं बिना वर्कफ़्लो बदले जोड़ी जा सकती हैं।",
    "landing.emergency":
      "अगर आप तुरंत शारीरिक खतरे में हैं, तो 112 पर कॉल करें। अभी हुई साइबर फ्रॉड के लिए, पहले यह टूल इस्तेमाल करने के बजाय तुरंत 1930 पर कॉल करें।",
    "landing.beforeTitle": "शुरू करने से पहले",
    "landing.beforeBody":
      "आप जो भी अपलोड या वर्णन करते हैं वह केवल आपके केस का विश्लेषण करने के लिए इस्तेमाल होता है। आप कभी भी केस और उसकी फाइलें डिलीट कर सकते हैं। यह टूल कानूनी जानकारी देता है, कानूनी सलाह नहीं — यह कभी तय नहीं करेगा कि सही कौन है, कोर्ट क्या करेगा, या आपकी ओर से कुछ दाख़िल नहीं करेगा।",
    "landing.whatHelp": "आपको किस बारे में मदद चाहिए?",
    "domain.rental": "किराया और मकान मालिक-किरायेदार",
    "domain.rentalDesc": "किराया नोटिस, बेदखली नोटिस, या डिपॉज़िट विवाद।",
    "domain.employment": "रोज़गार",
    "domain.employmentDesc": "ऑफर लेटर, वेतन कटौती, या नौकरी से निकाले जाने का नोटिस।",
    "domain.consumer": "उपभोक्ता विवाद",
    "domain.consumerDesc": "खराब उत्पाद, वारंटी समस्या, या सेवा शिकायत।",
    "domain.cyber": "साइबर धोखाधड़ी",
    "domain.cyberDesc": "ऑनलाइन धोखा, UPI फ्रॉड, या अकाउंट कॉम्प्रोमाइज़।",

    "newcase.title": "नया केस शुरू करें",
    "newcase.subtitle":
      "पहले चुनें कि यह किस बारे में है, फिर दस्तावेज़ अपलोड करें, जो हुआ उसे बताएं, या एक छोटी वॉइस नोट रिकॉर्ड करें।",
    "newcase.domainLabel": "यह किस बारे में है?",
    "newcase.describe": "बताएं",
    "newcase.upload": "दस्तावेज़ अपलोड करें",
    "newcase.voice": "वॉइस नोट रिकॉर्ड करें",
    "newcase.submit": "इस केस का विश्लेषण करें",

    "tab.overview": "हमें क्या मिला",
    "tab.facts": "इस्तेमाल की गई जानकारी",
    "tab.dates": "ज़रूरी तारीखें",
    "tab.action": "आगे क्या करें",
    "tab.evidence": "सबूत लॉकर",
    "tab.draft": "ड्राफ्ट सेंटर",

    "footer.disclaimer":
      "NyayaSetu कानूनी जानकारी और प्रक्रियात्मक मार्गदर्शन देता है, कानूनी सलाह नहीं। यह दोष तय नहीं करता, कोर्ट के फैसले का अनुमान नहीं लगाता, या आपकी ओर से कुछ दाख़िल नहीं करता।",
  },
  mr: {
    "nav.myCases": "माझी प्रकरणे",
    "nav.newCase": "नवीन प्रकरण",
    "nav.logout": "लॉग आउट",
    "nav.login": "लॉग इन",
    "nav.signup": "साइन अप",
    "nav.tagline": "प्रकरण होण्याआधी धोका समजून घ्या",

    "landing.eyebrow": "रोजच्या परिस्थितींसाठी एक प्रतिबंधात्मक कायदेशीर-जोखीम साधन",
    "landing.title": "कोर्ट प्रकरण होण्याआधी कायदेशीर धोका समजून घ्या.",
    "landing.subtitle":
      "एखादी नोटीस अपलोड करा किंवा काय घडलं ते सांगा. NyayaSetu साध्या भाषेत समजावतो, महत्त्वाच्या तारखा सांगतो, आणि योग्य सरकारी सेवेकडे मार्गदर्शन करतो — प्रत्येक माहिती स्रोतासह.",
    "landing.languageNote": "Bhashini च्या मदतीने वर्कफ्लो न बदलता आणखी भाषा जोडता येतील.",
    "landing.emergency":
      "जर तुम्ही तात्काळ शारीरिक धोक्यात असाल, तर 112 वर कॉल करा. नुकत्याच झालेल्या सायबर फसवणुकीसाठी, हे टूल वापरण्याआधी लगेच 1930 वर कॉल करा.",
    "landing.beforeTitle": "सुरुवात करण्यापूर्वी",
    "landing.beforeBody":
      "तुम्ही जे काही अपलोड किंवा वर्णन करता ते फक्त तुमच्या प्रकरणाचे विश्लेषण करण्यासाठी वापरले जाते. तुम्ही कधीही प्रकरण आणि त्याच्या फाइल्स डिलीट करू शकता. हे साधन कायदेशीर माहिती देते, कायदेशीर सल्ला नाही — हे कधीही कोण बरोबर आहे हे ठरवणार नाही, कोर्ट काय करेल याचा अंदाज लावणार नाही, किंवा तुमच्या वतीने काहीही दाखल करणार नाही.",
    "landing.whatHelp": "तुम्हाला कशाबद्दल मदत हवी आहे?",
    "domain.rental": "भाडे आणि घरमालक-भाडेकरू",
    "domain.rentalDesc": "भाडे नोटीस, बेदखली नोटीस, किंवा डिपॉझिट वाद.",
    "domain.employment": "रोजगार",
    "domain.employmentDesc": "ऑफर लेटर, पगार कपात, किंवा नोकरीवरून काढल्याची नोटीस.",
    "domain.consumer": "ग्राहक वाद",
    "domain.consumerDesc": "सदोष उत्पादन, वॉरंटी समस्या, किंवा सेवा तक्रार.",
    "domain.cyber": "सायबर फसवणूक",
    "domain.cyberDesc": "ऑनलाइन फसवणूक, UPI फ्रॉड, किंवा खाते तडजोड.",

    "newcase.title": "नवीन प्रकरण सुरू करा",
    "newcase.subtitle":
      "आधी हे कशाबद्दल आहे ते निवडा, मग दस्तऐवज अपलोड करा, काय घडलं ते सांगा, किंवा एक छोटी व्हॉइस नोट रेकॉर्ड करा.",
    "newcase.domainLabel": "हे कशाबद्दल आहे?",
    "newcase.describe": "सांगा",
    "newcase.upload": "दस्तऐवज अपलोड करा",
    "newcase.voice": "व्हॉइस नोट रेकॉर्ड करा",
    "newcase.submit": "या प्रकरणाचे विश्लेषण करा",

    "tab.overview": "आम्हाला काय सापडले",
    "tab.facts": "वापरलेली माहिती",
    "tab.dates": "महत्त्वाच्या तारखा",
    "tab.action": "पुढे काय करावे",
    "tab.evidence": "पुरावा लॉकर",
    "tab.draft": "ड्राफ्ट सेंटर",

    "footer.disclaimer":
      "NyayaSetu कायदेशीर माहिती आणि प्रक्रियात्मक मार्गदर्शन देते, कायदेशीर सल्ला नाही. हे दोष ठरवत नाही, कोर्टाच्या निकालाचा अंदाज लावत नाही, किंवा तुमच्या वतीने काहीही दाखल करत नाही.",
  },
} as const;

export type TranslationKey = keyof typeof translations.en;

interface LanguageContextValue {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: TranslationKey) => string;
}

const LanguageContext = createContext<LanguageContextValue | null>(null);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<Language>(() => {
    const stored = localStorage.getItem(LANG_KEY);
    return stored === "hi" || stored === "mr" ? stored : "en";
  });

  useEffect(() => {
    localStorage.setItem(LANG_KEY, language);
    document.documentElement.lang = language;
  }, [language]);

  function setLanguage(lang: Language) {
    setLanguageState(lang);
  }

  function t(key: TranslationKey): string {
    return translations[language][key] ?? translations.en[key] ?? key;
  }

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage(): LanguageContextValue {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error("useLanguage must be used inside LanguageProvider");
  return ctx;
}
