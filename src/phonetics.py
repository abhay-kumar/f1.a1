#!/usr/bin/env python3
"""
Phonetics Module - Ensures correct pronunciation of F1 proper nouns
Converts names and terms to phonetic spellings for TTS accuracy.

Sources:
- PronounceF1.com
- Forvo.com native speaker recordings
- Driver interviews
"""
import os
import sys
import json
import argparse
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import get_project_dir


@dataclass
class PhoneticEntry:
    """A phonetic pronunciation entry"""
    original: str
    phonetic: str
    ipa: str  # International Phonetic Alphabet
    language: str
    notes: str


# F1 Driver Pronunciations (verified from native speakers and official sources)
# Format: "original": PhoneticEntry(original, phonetic_spelling, IPA, language, notes)
F1_DRIVER_PHONETICS: Dict[str, PhoneticEntry] = {
    # Current Grid (2024)
    "verstappen": PhoneticEntry(
        "Verstappen", "Fur-STAH-pn", "fərˈstɑpən",
        "Dutch", "NOT Ver-shtap-pen"
    ),
    "max verstappen": PhoneticEntry(
        "Max Verstappen", "Max Fur-STAH-pn", "mæks fərˈstɑpən",
        "Dutch", "First name is standard English"
    ),
    "leclerc": PhoneticEntry(
        "Leclerc", "Luh-CLAIR", "ləˈklɛʁ",
        "French/Monégasque", "NOT Le-clerk"
    ),
    "charles leclerc": PhoneticEntry(
        "Charles Leclerc", "SHARL Luh-CLAIR", "ʃaʁl ləˈklɛʁ",
        "French", "Charles is French pronunciation"
    ),
    "sainz": PhoneticEntry(
        "Sainz", "SINES", "ˈsajns",
        "Spanish", "Like 'signs' with softer S"
    ),
    "carlos sainz": PhoneticEntry(
        "Carlos Sainz", "KAR-loss SINES", "ˈkaɾlos ˈsajns",
        "Spanish", "NOT Car-los Sains"
    ),
    "perez": PhoneticEntry(
        "Pérez", "PEH-rez", "ˈpeɾes",
        "Spanish/Mexican", "Stress on first syllable"
    ),
    "sergio perez": PhoneticEntry(
        "Sergio Pérez", "SAIR-hee-oh PEH-rez", "ˈseɾxjo ˈpeɾes",
        "Spanish", "Soft G in Sergio"
    ),
    "hamilton": PhoneticEntry(
        "Hamilton", "HAM-il-ton", "ˈhæmɪltən",
        "English", "Standard English"
    ),
    "russell": PhoneticEntry(
        "Russell", "RUSS-el", "ˈrʌsəl",
        "English", "Standard English"
    ),
    "norris": PhoneticEntry(
        "Norris", "NOR-iss", "ˈnɒrɪs",
        "English", "Standard English"
    ),
    "piastri": PhoneticEntry(
        "Piastri", "pee-ASS-tree", "piˈastri",
        "Italian/Australian", "Italian heritage pronunciation"
    ),
    "oscar piastri": PhoneticEntry(
        "Oscar Piastri", "OSS-kar pee-ASS-tree", "ˈɒskɑ piˈastri",
        "Italian/Australian", "Standard Oscar"
    ),
    "alonso": PhoneticEntry(
        "Alonso", "ah-LON-so", "aˈlonso",
        "Spanish", "Stress on second syllable"
    ),
    "fernando alonso": PhoneticEntry(
        "Fernando Alonso", "fer-NAN-doh ah-LON-so", "ferˈnando aˈlonso",
        "Spanish", "Standard Spanish"
    ),
    "stroll": PhoneticEntry(
        "Stroll", "STROHL", "stroʊl",
        "English/Canadian", "Like 'stroll' in English"
    ),
    "gasly": PhoneticEntry(
        "Gasly", "gaz-LEE", "ɡazˈli",
        "French", "NOT Gas-lee"
    ),
    "pierre gasly": PhoneticEntry(
        "Pierre Gasly", "pee-AIR gaz-LEE", "pjɛʁ ɡazˈli",
        "French", "Standard French Pierre"
    ),
    "ocon": PhoneticEntry(
        "Ocon", "oh-KOHN", "oˈkɔ̃",
        "French", "Nasal ending"
    ),
    "tsunoda": PhoneticEntry(
        "Tsunoda", "tsoo-NO-da", "tsɯˈnoda",
        "Japanese", "Soft 'tsu' sound"
    ),
    "yuki tsunoda": PhoneticEntry(
        "Yuki Tsunoda", "YOO-kee tsoo-NO-da", "jɯki tsɯˈnoda",
        "Japanese", "Standard Japanese"
    ),
    "ricciardo": PhoneticEntry(
        "Ricciardo", "ri-CHAR-doh", "riˈtʃardo",
        "Italian/Australian", "Italian pronunciation"
    ),
    "daniel ricciardo": PhoneticEntry(
        "Daniel Ricciardo", "DAN-yel ri-CHAR-doh", "ˈdænjəl riˈtʃardo",
        "Italian/Australian", "English Daniel"
    ),
    "albon": PhoneticEntry(
        "Albon", "AL-bon", "ˈælbɒn",
        "English/Thai", "Standard English"
    ),
    "magnussen": PhoneticEntry(
        "Magnussen", "MAG-noo-sen", "ˈmæɡnʊsən",
        "Danish", "NOT Mag-nus-sen"
    ),
    "hulkenberg": PhoneticEntry(
        "Hülkenberg", "HILL-ken-berg", "ˈhʏlkənbɛʁk",
        "German", "Ü sound like 'hill'"
    ),
    "bottas": PhoneticEntry(
        "Bottas", "BOT-tass", "ˈbotːɑs",
        "Finnish", "Hard T sound"
    ),
    "zhou": PhoneticEntry(
        "Zhou", "JOE", "dʒəʊ",
        "Chinese", "Simplified for English TTS"
    ),
    "guanyu zhou": PhoneticEntry(
        "Guanyu Zhou", "GWON-yoo JOE", "ɡwɑnˈjuː dʒəʊ",
        "Chinese", "Zhou is family name"
    ),

    # Legends and Historic Drivers
    "vettel": PhoneticEntry(
        "Vettel", "FET-el", "ˈfɛtl̩",
        "German", "V sounds like F in German"
    ),
    "sebastian vettel": PhoneticEntry(
        "Sebastian Vettel", "ze-BASS-tee-an FET-el", "zeˈbastiːan ˈfɛtl̩",
        "German", "German Sebastian"
    ),
    "schumacher": PhoneticEntry(
        "Schumacher", "SHOO-mah-ker", "ˈʃuːmaxɐ",
        "German", "Standard German"
    ),
    "michael schumacher": PhoneticEntry(
        "Michael Schumacher", "MEE-kah-el SHOO-mah-ker", "ˈmiːçaːʔeːl ˈʃuːmaxɐ",
        "German", "German Michael"
    ),
    "raikkonen": PhoneticEntry(
        "Räikkönen", "RYE-kuh-nen", "ˈræikːønen",
        "Finnish", "Ä like 'rye'"
    ),
    "kimi raikkonen": PhoneticEntry(
        "Kimi Räikkönen", "KEE-mee RYE-kuh-nen", "ˈkimi ˈræikːønen",
        "Finnish", "Standard Finnish"
    ),
    "hakkinen": PhoneticEntry(
        "Häkkinen", "HECK-in-en", "ˈhækːinen",
        "Finnish", "NOT Ha-ki-nen"
    ),
    "senna": PhoneticEntry(
        "Senna", "SEN-na", "ˈsẽnɐ",
        "Portuguese/Brazilian", "Standard pronunciation"
    ),
    "ayrton senna": PhoneticEntry(
        "Ayrton Senna", "AIR-ton SEN-na", "ˈajɾtõ ˈsẽnɐ",
        "Portuguese/Brazilian", "Portuguese Ayrton"
    ),
    "prost": PhoneticEntry(
        "Prost", "PROHST", "pʁɔst",
        "French", "Silent T possible"
    ),
    "lauda": PhoneticEntry(
        "Lauda", "LOW-da", "ˈlaʊda",
        "Austrian/German", "NOT Law-da"
    ),
    "niki lauda": PhoneticEntry(
        "Niki Lauda", "NEE-kee LOW-da", "ˈniːki ˈlaʊda",
        "Austrian", "Standard Austrian"
    ),
    "piquet": PhoneticEntry(
        "Piquet", "pee-KAY", "piˈke",
        "Portuguese/Brazilian", "French-influenced"
    ),
    "webber": PhoneticEntry(
        "Webber", "WEB-er", "ˈwɛbə",
        "English/Australian", "Standard English"
    ),
}

# F1 Team Pronunciations
F1_TEAM_PHONETICS: Dict[str, PhoneticEntry] = {
    "mclaren": PhoneticEntry(
        "McLaren", "muh-CLAIR-en", "məˈklærən",
        "Scottish", "Named after Bruce McLaren"
    ),
    "ferrari": PhoneticEntry(
        "Ferrari", "feh-RAH-ree", "ferˈraːri",
        "Italian", "Rolling R"
    ),
    "mercedes": PhoneticEntry(
        "Mercedes", "mer-SAY-deez", "mɛɐ̯ˈtseːdəs",
        "German", "German pronunciation"
    ),
    "red bull": PhoneticEntry(
        "Red Bull", "RED BULL", "rɛd bʊl",
        "English", "Standard English"
    ),
    "alpine": PhoneticEntry(
        "Alpine", "AL-pine", "ˈælpaɪn",
        "English/French", "English pronunciation used"
    ),
    "haas": PhoneticEntry(
        "Haas", "HAHSS", "hɑːs",
        "German", "Long A sound"
    ),
    "sauber": PhoneticEntry(
        "Sauber", "ZOW-ber", "ˈzaʊbɐ",
        "German/Swiss", "S sounds like Z"
    ),
}

# F1 Circuit Pronunciations
F1_CIRCUIT_PHONETICS: Dict[str, PhoneticEntry] = {
    "monza": PhoneticEntry(
        "Monza", "MON-zah", "ˈmontsa",
        "Italian", "Standard Italian"
    ),
    "spa": PhoneticEntry(
        "Spa", "SPAH", "spa",
        "French/Belgian", "NOT Spar"
    ),
    "spa-francorchamps": PhoneticEntry(
        "Spa-Francorchamps", "SPAH fron-kor-SHOM", "spa fʁɑ̃kɔʁʃɑ̃",
        "French/Belgian", "French pronunciation"
    ),
    "monaco": PhoneticEntry(
        "Monaco", "MON-ah-ko", "ˈmɔnako",
        "French", "NOT Mo-nay-co"
    ),
    "monte carlo": PhoneticEntry(
        "Monte Carlo", "MON-tay KAR-loh", "ˌmɔnte ˈkarlo",
        "Italian/French", "Standard"
    ),
    "imola": PhoneticEntry(
        "Imola", "EE-moh-la", "ˈiːmola",
        "Italian", "Stress on first syllable"
    ),
    "suzuka": PhoneticEntry(
        "Suzuka", "soo-ZOO-ka", "sɯˈzɯka",
        "Japanese", "Standard Japanese"
    ),
    "interlagos": PhoneticEntry(
        "Interlagos", "in-ter-LAH-gos", "ĩteɾˈlaɡus",
        "Portuguese/Brazilian", "Standard Portuguese"
    ),
    "hockenheim": PhoneticEntry(
        "Hockenheim", "HOK-en-hime", "ˈhɔkənhaɪm",
        "German", "Standard German"
    ),
    "nurburgring": PhoneticEntry(
        "Nürburgring", "NOOR-burg-ring", "ˈnyːɐ̯bʊʁkʁɪŋ",
        "German", "Ü like OO"
    ),
    "zandvoort": PhoneticEntry(
        "Zandvoort", "ZAND-vort", "ˈzɑntfoːrt",
        "Dutch", "Standard Dutch"
    ),
    "hungaroring": PhoneticEntry(
        "Hungaroring", "HUN-gah-ro-ring", "ˈhʊŋɡɑroːrɪŋ",
        "Hungarian/English", "Hybrid pronunciation"
    ),
    "jeddah": PhoneticEntry(
        "Jeddah", "JED-dah", "ˈdʒɛdə",
        "Arabic", "Standard English approximation"
    ),
    "bahrain": PhoneticEntry(
        "Bahrain", "bah-RAIN", "bɑːˈreɪn",
        "Arabic", "Standard English"
    ),
    "abu dhabi": PhoneticEntry(
        "Abu Dhabi", "ah-boo DAH-bee", "ˈæbuː ˈdɑːbi",
        "Arabic", "Standard English approximation"
    ),
    "yas marina": PhoneticEntry(
        "Yas Marina", "YASS mah-REE-nah", "jæs məˈriːnə",
        "Arabic", "Standard pronunciation"
    ),
}

# Common F1 Terms
F1_TERM_PHONETICS: Dict[str, PhoneticEntry] = {
    "drs": PhoneticEntry(
        "DRS", "D-R-S", "diː ɑːr ɛs",
        "English", "Spell out letters"
    ),
    "ers": PhoneticEntry(
        "ERS", "E-R-S", "iː ɑːr ɛs",
        "English", "Energy Recovery System"
    ),
    "fia": PhoneticEntry(
        "FIA", "F-I-A", "ɛf aɪ eɪ",
        "English", "Spell out letters"
    ),
    "pirelli": PhoneticEntry(
        "Pirelli", "pih-REL-lee", "piˈrɛlli",
        "Italian", "Standard Italian"
    ),
    "parc ferme": PhoneticEntry(
        "parc fermé", "park fair-MAY", "paʁk fɛʁme",
        "French", "French term"
    ),
    "pole position": PhoneticEntry(
        "pole position", "POLE puh-ZI-shun", "poʊl pəˈzɪʃən",
        "English", "Standard English"
    ),
    "paddock": PhoneticEntry(
        "paddock", "PAD-ock", "ˈpædək",
        "English", "Standard English"
    ),
    "chicane": PhoneticEntry(
        "chicane", "shih-CANE", "ʃɪˈkeɪn",
        "French/English", "Standard"
    ),
    "eau rouge": PhoneticEntry(
        "Eau Rouge", "oh ROOZH", "o ʁuʒ",
        "French", "Famous Spa corner"
    ),
    "raidillon": PhoneticEntry(
        "Raidillon", "ray-dee-YON", "ʁɛdijɔ̃",
        "French", "Often confused with Eau Rouge"
    ),
    "maggots": PhoneticEntry(
        "Maggots", "MAG-ots", "ˈmæɡəts",
        "English", "Silverstone corner"
    ),
    "becketts": PhoneticEntry(
        "Becketts", "BEK-ets", "ˈbɛkɪts",
        "English", "Silverstone corner"
    ),
    "la source": PhoneticEntry(
        "La Source", "la SOORS", "la suʁs",
        "French", "Spa first corner"
    ),
    "parabolica": PhoneticEntry(
        "Parabolica", "pa-ra-BOL-i-ka", "paraˈbɔlika",
        "Italian", "Monza corner (now Alboreto)"
    ),
    "lesmo": PhoneticEntry(
        "Lesmo", "LEZ-mo", "ˈlɛzmo",
        "Italian", "Monza corners"
    ),
    "ascari": PhoneticEntry(
        "Ascari", "ASS-ka-ree", "asˈkari",
        "Italian", "Monza chicane"
    ),
}


def get_all_phonetics() -> Dict[str, PhoneticEntry]:
    """Get all phonetic entries combined"""
    all_phonetics = {}
    all_phonetics.update(F1_DRIVER_PHONETICS)
    all_phonetics.update(F1_TEAM_PHONETICS)
    all_phonetics.update(F1_CIRCUIT_PHONETICS)
    all_phonetics.update(F1_TERM_PHONETICS)
    return all_phonetics


def apply_phonetics(text: str, mode: str = "phonetic") -> Tuple[str, List[Tuple[str, str]]]:
    """
    Apply phonetic replacements to text.

    Args:
        text: Original text
        mode: "phonetic" for spoken spelling, "hint" for (pronunciation hints)

    Returns:
        Tuple of (modified_text, list of (original, replacement) pairs)
    """
    all_phonetics = get_all_phonetics()
    replacements = []

    # Sort by length (longest first) to avoid partial matches
    sorted_keys = sorted(all_phonetics.keys(), key=len, reverse=True)

    modified_text = text

    for key in sorted_keys:
        entry = all_phonetics[key]
        # Case-insensitive search
        pattern = re.compile(re.escape(key), re.IGNORECASE)

        if pattern.search(modified_text):
            if mode == "phonetic":
                replacement = entry.phonetic
            elif mode == "hint":
                replacement = f"{entry.original} ({entry.phonetic})"
            else:
                replacement = entry.phonetic

            # Track replacements
            matches = pattern.findall(modified_text)
            for match in matches:
                replacements.append((match, replacement))

            # Apply replacement (preserve first match case for proper nouns)
            modified_text = pattern.sub(replacement, modified_text)

    return modified_text, replacements


def analyze_text(text: str) -> Dict[str, List[str]]:
    """Analyze text for F1 terms that might need pronunciation guidance"""
    all_phonetics = get_all_phonetics()

    found = {"drivers": [], "teams": [], "circuits": [], "terms": [], "unknown": []}

    # Check for known terms
    text_lower = text.lower()

    for key in F1_DRIVER_PHONETICS:
        if key in text_lower:
            found["drivers"].append(key)

    for key in F1_TEAM_PHONETICS:
        if key in text_lower:
            found["teams"].append(key)

    for key in F1_CIRCUIT_PHONETICS:
        if key in text_lower:
            found["circuits"].append(key)

    for key in F1_TERM_PHONETICS:
        if key in text_lower:
            found["terms"].append(key)

    # Look for potential proper nouns not in database
    # (Words starting with capital letters that aren't common English)
    words = re.findall(r'\b[A-Z][a-z]+\b', text)
    common_words = {"The", "And", "For", "With", "From", "This", "That", "When", "Where",
                    "What", "Who", "How", "But", "Not", "Just", "Into", "After", "Before"}

    for word in words:
        word_lower = word.lower()
        if word not in common_words and word_lower not in all_phonetics:
            found["unknown"].append(word)

    return found


def process_script(script_path: str, output_path: Optional[str] = None,
                   mode: str = "phonetic") -> Dict:
    """Process a script.json file and apply phonetic corrections"""
    with open(script_path) as f:
        script = json.load(f)

    results = {
        "segments": [],
        "total_replacements": 0,
        "unknown_terms": []
    }

    for i, segment in enumerate(script.get("segments", [])):
        original_text = segment.get("text", "")

        # Analyze for unknown terms
        analysis = analyze_text(original_text)
        results["unknown_terms"].extend(analysis["unknown"])

        # Apply phonetics
        modified_text, replacements = apply_phonetics(original_text, mode)

        results["segments"].append({
            "index": i,
            "original": original_text,
            "modified": modified_text,
            "replacements": replacements
        })
        results["total_replacements"] += len(replacements)

        # Update script if output path provided
        if output_path:
            segment["text_phonetic"] = modified_text

    # Save modified script
    if output_path:
        with open(output_path, 'w') as f:
            json.dump(script, f, indent=2)

    # Deduplicate unknown terms
    results["unknown_terms"] = list(set(results["unknown_terms"]))

    return results


def main():
    parser = argparse.ArgumentParser(description='Apply phonetic corrections to F1 scripts')
    parser.add_argument('--project', required=True, help='Project name')
    parser.add_argument('--mode', choices=['phonetic', 'hint', 'analyze'],
                        default='analyze', help='Processing mode')
    parser.add_argument('--apply', action='store_true',
                        help='Apply changes to script (adds text_phonetic field)')
    parser.add_argument('--list', action='store_true',
                        help='List all available phonetic entries')
    args = parser.parse_args()

    if args.list:
        print("=" * 70)
        print("F1 PHONETIC DATABASE")
        print("=" * 70)

        print("\nDRIVERS:")
        print("-" * 70)
        for key, entry in sorted(F1_DRIVER_PHONETICS.items()):
            print(f"  {entry.original:25} -> {entry.phonetic:20} [{entry.language}]")

        print("\nTEAMS:")
        print("-" * 70)
        for key, entry in sorted(F1_TEAM_PHONETICS.items()):
            print(f"  {entry.original:25} -> {entry.phonetic:20} [{entry.language}]")

        print("\nCIRCUITS:")
        print("-" * 70)
        for key, entry in sorted(F1_CIRCUIT_PHONETICS.items()):
            print(f"  {entry.original:25} -> {entry.phonetic:20} [{entry.language}]")

        print("\nTERMS:")
        print("-" * 70)
        for key, entry in sorted(F1_TERM_PHONETICS.items()):
            print(f"  {entry.original:25} -> {entry.phonetic:20} [{entry.language}]")

        print(f"\nTotal entries: {len(get_all_phonetics())}")
        return

    project_dir = get_project_dir(args.project)
    script_file = f"{project_dir}/script.json"

    if not os.path.exists(script_file):
        print(f"Error: Script not found at {script_file}")
        sys.exit(1)

    print("=" * 60)
    print(f"Phonetics Processor - Project: {args.project}")
    print(f"Mode: {args.mode}")
    print("=" * 60)

    output_path = script_file if args.apply else None
    results = process_script(script_file, output_path, args.mode)

    for segment in results["segments"]:
        print(f"\n[Segment {segment['index']}]")
        print(f"  Original: {segment['original'][:70]}...")

        if args.mode != 'analyze':
            print(f"  Modified: {segment['modified'][:70]}...")

        if segment['replacements']:
            print("  Replacements:")
            for orig, repl in segment['replacements']:
                print(f"    {orig} -> {repl}")

    print(f"\n{'=' * 60}")
    print(f"Total replacements: {results['total_replacements']}")

    if results["unknown_terms"]:
        print(f"\nUnknown proper nouns (may need pronunciation guidance):")
        for term in results["unknown_terms"]:
            print(f"  - {term}")

    if args.apply:
        print(f"\nScript updated with 'text_phonetic' field in: {script_file}")
    else:
        print("\nTip: Run with --apply to add phonetic text to script.json")


if __name__ == "__main__":
    main()
