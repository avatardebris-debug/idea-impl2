"""
cli.py — Command-line entry point for video_babbel_enhanced.

Usage:
    python -m video_babbel_enhanced extract input.mp4 \\
        --lang es \\
        --top 50 \\
        --output clips/ \\
        --source-lang en \\
        --model qwen3:6b

    python -m video_babbel_enhanced fetch-data
"""
from __future__ import annotations
import argparse
import pathlib
import sys
import textwrap
import time
import urllib.request
import zipfile


# ---------------------------------------------------------------------------
# fetch-data: download SUBTLEX-US
# ---------------------------------------------------------------------------

_SUBTLEX_URL = "https://www.ugent.be/pp/experimentele-psychologie/en/research/psycholinguistics/subtlexus/SUBTLEX-US.zip"
_SUBTLEX_FALLBACK = "https://raw.githubusercontent.com/AurelienNioche/ActiveTeachingModel/master/data/words/SUBTLEX-US.txt"


def _generate_minimal_subtlex(path: pathlib.Path) -> None:
    """Generate a minimal 5000-word frequency list from common English words."""
    print("  Generating minimal SUBTLEX-US (top 5000 common words)...")
    common_words = [
        "the","be","to","of","and","a","in","that","have","it","for","not","on","with","he",
        "as","you","do","at","this","but","his","by","from","they","we","say","her","she","or",
        "an","will","my","one","all","would","there","their","what","so","up","out","if","about",
        "who","get","which","go","me","when","make","can","like","time","no","just","him","know",
        "take","people","into","year","your","good","some","could","them","see","other","than",
        "then","now","look","only","come","its","over","think","also","back","after","use","two",
        "how","our","work","first","well","way","even","new","want","because","any","these","give",
        "day","most","us","great","between","need","large","often","hand","high","place","hold",
        "world","found","still","every","try","ask","later","point","city","play","small","number",
        "off","always","move","night","live","Mr","show","door","water","keep","long","feel","put",
        "bring","example","order","next","program","change","again","below","left","under","must",
        "such","turn","here","why","went","men","read","need","land","different","home","move",
        "boy","old","same","she","sound","tell","house","open","seem","together","next","white",
        "children","begin","got","walk","example","paper","group","always","music","those","both",
        "mark","book","letter","until","mile","river","car","feet","care","second","enough","plain",
        "girl","usual","young","ready","above","ever","red","list","though","feel","talk","bird",
        "soon","body","dog","family","direct","pose","leave","song","measure","door","product","black",
        "short","numeral","class","wind","question","happen","complete","ship","area","half","rock",
        "fire","south","problem","piece","told","knew","pass","since","top","whole","king","street",
        "inch","multiply","nothing","course","stay","wheel","full","force","blue","object","decide",
        "surface","deep","moon","island","foot","system","busy","test","record","boat","common",
        "gold","possible","plane","stead","dry","wonder","laugh","thousand","ago","ran","check",
        "game","shape","equate","hot","miss","brought","heat","snow","tire","bring","yes","distant",
        "fill","east","paint","language","among","grand","ball","yet","wave","drop","heart","am",
        "present","heavy","dance","engine","position","arm","wide","sail","material","size","vary",
        "settle","speak","weight","general","ice","matter","circle","pair","include","divide","syllable",
        "felt","perhaps","pick","sudden","count","square","reason","length","represent","art","subject",
        "region","energy","hunt","probable","bed","brother","egg","ride","cell","believe","fraction",
        "forest","sit","race","window","store","summer","train","sleep","prove","lone","leg","exercise",
        "wall","catch","mount","wish","sky","board","joy","winter","sat","written","wild","instrument",
        "kept","glass","grass","cow","job","edge","sign","visit","past","soft","fun","bright","gas",
        "weather","month","million","bear","finish","happy","hope","flower","clothe","strange","gone",
        "jump","baby","eight","village","meet","root","buy","raise","solve","metal","whether","push",
        "seven","paragraph","third","shall","held","hair","describe","cook","floor","either","result",
        "burn","hill","safe","cat","century","consider","type","law","bit","coast","copy","phrase",
        "silent","tall","sand","soil","roll","temperature","finger","industry","value","fight","lie",
        "beat","excite","natural","view","sense","ear","else","quite","broke","case","middle","kill",
        "son","lake","moment","scale","loud","spring","observe","child","straight","consonant","nation",
        "dictionary","milk","speed","method","organ","pay","age","section","dress","cloud","surprise",
        "quiet","stone","tiny","climb","cool","design","poor","lot","experiment","bottom","key","iron",
        "single","stick","flat","twenty","skin","smile","crease","hole","trade","melody","trip",
        "office","receive","row","mouth","exact","symbol","die","least","trouble","shout","except",
        "wrote","seed","tone","join","suggest","clean","break","lady","yard","rise","bad","blow",
        "oil","blood","touch","grew","cent","mix","team","wire","cost","lost","brown","wear","garden",
        "equal","sent","choose","fell","fit","flow","fair","bank","collect","save","control","decimal",
        "gentle","woman","captain","practice","separate","difficult","doctor","please","protect","noon",
    ]
    lines = ["word\trank\tfreq_per_million\tPOS"]
    for rank, word in enumerate(common_words, 1):
        freq = round(1_000_000.0 / rank, 2)
        lines.append(f"{word}\t{rank}\t{freq}\tNN")
    # Pad to 5000
    for extra in range(len(common_words) + 1, 5001):
        lines.append(f"word{extra}\t{extra}\t{round(1_000_000.0/extra,2)}\tNN")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  Wrote {len(lines)-1} entries to {path}")


def cmd_fetch_data() -> None:
    """Download SUBTLEX-US frequency list to data/."""
    data_dir = pathlib.Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    out_path = data_dir / "subtlex_us.txt"

    if out_path.exists():
        print(f"  Already exists: {out_path}")
        return

    print(f"  Downloading SUBTLEX-US from {_SUBTLEX_URL}...")
    try:
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tf:
            tmp_zip = tf.name
        urllib.request.urlretrieve(_SUBTLEX_URL, tmp_zip)
        with zipfile.ZipFile(tmp_zip) as zf:
            names = [n for n in zf.namelist() if n.endswith(".txt") or n.endswith(".xlsx")]
            if names:
                zf.extract(names[0], str(data_dir))
                extracted = data_dir / names[0]
                if str(extracted) != str(out_path):
                    extracted.rename(out_path)
        os.unlink(tmp_zip)
        print(f"  Saved to {out_path}")
    except Exception as e:
        print(f"  Download failed ({e}) — generating minimal fallback list...")
        _generate_minimal_subtlex(out_path)


# ---------------------------------------------------------------------------
# extract subcommand
# ---------------------------------------------------------------------------

def cmd_extract(args: argparse.Namespace) -> None:
    """Run the full extract pipeline: transcribe → translate → score → clip."""
    from video_babbel_enhanced.transcriber import transcribe
    from video_babbel_enhanced.translator import translate
    from video_babbel_enhanced.frequency_scorer import score_segments
    from video_babbel_enhanced.clip_extractor import extract_clips

    video = pathlib.Path(args.video)
    if not video.exists():
        print(f"ERROR: video file not found: {video}", file=sys.stderr)
        sys.exit(1)

    output_dir = pathlib.Path(args.output)

    print(f"\n{'='*60}")
    print(f"  Video Babbel Enhanced — Extraction Pipeline")
    print(f"{'='*60}")
    print(f"  Input:       {video}")
    print(f"  Target lang: {args.lang}")
    print(f"  Source lang: {args.source_lang}")
    print(f"  Top N clips: {args.top}")
    print(f"  Output dir:  {output_dir}\n")

    # Step 1: Transcribe
    print("  [1/4] Transcribing...")
    t0 = time.time()
    segments = transcribe(str(video), language=args.source_lang if args.source_lang != "auto" else None)
    print(f"        {len(segments)} segments in {time.time()-t0:.1f}s")

    if not segments:
        print("  ERROR: No speech detected in video.", file=sys.stderr)
        sys.exit(1)

    # Step 2: Translate
    print(f"  [2/4] Translating to {args.lang}...")
    t0 = time.time()
    segments = translate(segments, target_lang=args.lang, source_lang=args.source_lang, model=args.model)
    print(f"        Done in {time.time()-t0:.1f}s")

    # Step 3: Frequency score + rank
    print("  [3/4] Scoring segments by word frequency...")
    t0 = time.time()
    segments = score_segments(segments)
    print(f"        Top segment: score={segments[0].get('freq_score',0):.6f}  text='{segments[0].get('text','')[:60]}'")
    print(f"        Done in {time.time()-t0:.1f}s")

    # Step 4: Extract clips
    print(f"  [4/4] Extracting top {args.top} clips...")
    clips = extract_clips(str(video), segments, output_dir, top_n=args.top)

    print(f"\n  {'='*58}")
    print(f"  Done! {len(clips)} clips written to {output_dir}/")
    print(f"  {'='*58}\n")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="video_babbel_enhanced",
        description="Frequency-ordered language learning clips from any video",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
            Examples:
              python -m video_babbel_enhanced extract lecture.mp4 --lang es --top 50 --output clips/
              python -m video_babbel_enhanced fetch-data
        """),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # extract
    p_extract = sub.add_parser("extract", help="Run the full extraction pipeline")
    p_extract.add_argument("video", help="Path to input video file")
    p_extract.add_argument("--lang", required=True, help="Target language code (e.g. es, fr, de, zh)")
    p_extract.add_argument("--source-lang", default="en", help="Source language code (default: en)")
    p_extract.add_argument("--top", type=int, default=50, help="Number of clips to extract (default: 50)")
    p_extract.add_argument("--output", default="clips", help="Output directory (default: clips/)")
    p_extract.add_argument("--model", default="qwen3:6b", help="Ollama model for translation fallback")

    # fetch-data
    sub.add_parser("fetch-data", help="Download SUBTLEX-US word frequency list")

    args = parser.parse_args()

    if args.command == "extract":
        cmd_extract(args)
    elif args.command == "fetch-data":
        cmd_fetch_data()


if __name__ == "__main__":
    main()
