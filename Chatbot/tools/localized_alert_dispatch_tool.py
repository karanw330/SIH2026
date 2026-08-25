import json


def localized_alert_dispatch_tool(district_name: str, risk_score: float, hazard_type: str = "Landslide Warning") -> str:
    """
    Generates localized SMS templates in English, Assamese, Khasi, and Hindi 
    and simulates dispatch to district officials and transport unions.

    Args:
        district_name: Name of affected district (e.g. "Upper Siang")
        risk_score: Current calculated risk probability (0.0 to 1.0)
        hazard_type: Nature of hazard (e.g. "Debris Flow", "Flash Flood")
    """
    # Generate SMS alerts per language format
    messages = {
        "English": f"EMERGENCY ALERT [{district_name}]: High {hazard_type} threat detected (Risk Level: {int(risk_score * 100)}%). NH route restricted. Avoid travel.",
        "Assamese": f"জৰুৰী সতৰ্কবাণী [{district_name}]: ভূমিস্খলনৰ প্ৰবল সম্ভাৱনা (সংকটৰ মাত্ৰা: {int(risk_score * 100)}%)। যাতায়াত স্থগিত ৰাখক।",
        "Khasi": f"SYNJOR BAD KYNMAW [{district_name}]: Ka jingma na ka jingtllun khyndew (Level: {int(risk_score * 100)}%). Pynsepia ka leit ka wan.",
        "Hindi": f"आपातकालीन चेतावनी [{district_name}]: भूस्खलन का उच्च खतरा (जोखिम स्तर: {int(risk_score * 100)}%)। मुख्य मार्ग का प्रयोग न करें।"
    }

    dispatch_summary = {
        "status": "DISPATCHED",
        "target_district": district_name,
        "risk_level_percent": round(risk_score * 100, 1),
        "recipients": ["District Disaster Officers", "Transport Union Heads", "Village Pradhans"],
        "dispatched_templates": messages
    }

    return json.dumps(dispatch_summary, ensure_ascii=False)
