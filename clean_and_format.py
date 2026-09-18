import os
import json
import random
import re
from pathlib import Path

random.seed(42)

OUTPUT_TRAIN = "./train.jsonl"
OUTPUT_VAL = "./val.jsonl"
VAL_SPLIT = 0.1

# Bilingual system prompt optimized for German + English job markets
SYSTEM_PROMPT = (
    "You are an expert HR recruiter and resume writer with 15+ years of experience "
    "at top tech companies in Germany and internationally. You specialize in both German "
    "(Lebenslauf, Anschreiben) and English (Resume, Cover Letter) job applications. "
    "You understand German job market conventions: formal tone, structured Lebenslauf format, "
    "professional photo requirements, and ATS optimization for both German and English systems. "
    "Always respond in the same language as the user's query. When generating resumes or cover "
    "letters, output strictly valid JSON matching the requested schema. Never add markdown "
    "formatting outside the JSON structure."
)

def clean_text(text):
    """Clean and normalize text"""
    if not text or not isinstance(text, str):
        return ""
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
    return text[:8000]

def load_json_file(filepath):
    """Load a single JSON file"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️  Error loading {filepath}: {e}")
        return None

def process_resume_score_details():
    """Process resume-score-details dataset (match/mismatch JSON files)"""
    print("📦 Processing resume-score-details...")
    ds_path = "./datasets/resume-score-details"
    pairs = []
    
    if not os.path.exists(ds_path):
        print("   ⚠️  Dataset not found")
        return pairs
    
    json_files = [f for f in os.listdir(ds_path) if f.endswith('.json')]
    
    for filename in json_files:
        filepath = os.path.join(ds_path, filename)
        data = load_json_file(filepath)
        
        if not data or 'input' not in data or 'output' not in data:
            continue
        
        # Determine type from filename
        is_match = filename.startswith('match_')
        is_mismatch = filename.startswith('mismatch_')
        is_invalid = filename.startswith('invalid_')
        is_empty = filename.startswith('empty_')
        
        # Skip invalid/empty files
        if is_invalid or is_empty:
            continue
        
        input_data = data['input']
        output_data = data['output']
        details = data.get('details', '')
        
        # Extract resume and job description from input
        resume_text = ""
        jd_text = ""
        
        if isinstance(input_data, dict):
            resume_text = input_data.get('resume', input_data.get('cv', ''))
            jd_text = input_data.get('job_description', input_data.get('jd', ''))
        elif isinstance(input_data, str):
            if 'resume' in input_data.lower():
                resume_text = input_data
            if 'job' in input_data.lower():
                jd_text = input_data
        
        if not resume_text or not jd_text:
            continue
        
        # Create training pair based on match/mismatch
        if is_match:
            user_msg = (
                f"Analyze this resume against the job description and provide detailed HR feedback.\n\n"
                f"JOB DESCRIPTION:\n{clean_text(jd_text)}\n\n"
                f"RESUME:\n{clean_text(resume_text)}"
            )
            assistant_msg = (
                f"{clean_text(details)}\n\n"
                f"**Match Assessment:** This resume shows strong alignment with the job requirements. "
                f"The candidate's skills and experience directly match the role's needs. "
                f"**Recommendations:** Highlight quantified achievements, ensure ATS-friendly formatting, "
                f"and tailor the summary to emphasize the most relevant experience."
            ) if details else (
                f"**Match Assessment:** This resume shows strong alignment with the job requirements. "
                f"The candidate's skills and experience directly match the role's needs. "
                f"**Recommendations:** Highlight quantified achievements, ensure ATS-friendly formatting, "
                f"and tailor the summary to emphasize the most relevant experience."
            )
        else:  # mismatch
            user_msg = (
                f"Analyze this resume against the job description and provide detailed HR feedback.\n\n"
                f"JOB DESCRIPTION:\n{clean_text(jd_text)}\n\n"
                f"RESUME:\n{clean_text(resume_text)}"
            )
            assistant_msg = (
                f"{clean_text(details)}\n\n"
                f"**Match Assessment:** This resume shows gaps when compared to the job requirements. "
                f"**Key Gaps:** The candidate's experience doesn't fully align with the core requirements. "
                f"**Recommendations:** Consider upskilling in the required areas, highlighting transferable skills, "
                f"or targeting roles that better match your current profile."
            ) if details else (
                f"**Match Assessment:** This resume shows gaps when compared to the job requirements. "
                f"**Key Gaps:** The candidate's experience doesn't fully align with the core requirements. "
                f"**Recommendations:** Consider upskilling in the required areas, highlighting transferable skills, "
                f"or targeting roles that better match your current profile."
            )
        
        pairs.append({
            'type': 'resume_feedback',
            'user': user_msg,
            'assistant': assistant_msg
        })
    
    print(f"   ✅ Extracted {len(pairs)} pairs")
    return pairs

def process_role_radar():
    """Process role-radar dataset (structured pairs + labels + jobs + profiles)"""
    print("📦 Processing role-radar...")
    ds_path = "./datasets/role-radar"
    pairs = []
    
    if not os.path.exists(ds_path):
        print("   ⚠️  Dataset not found")
        return pairs
    
    # Load all required files
    pairs_file = os.path.join(ds_path, 'phase3_pairs.json')
    labels_file = os.path.join(ds_path, 'phase3_labels.json')
    jobs_file = os.path.join(ds_path, 'scraped_jobs.json')
    profiles_file = os.path.join(ds_path, 'synthetic_profiles.json')
    
    pairs_data = load_json_file(pairs_file) or []
    labels_data = load_json_file(labels_file) or []
    jobs_data = load_json_file(jobs_file) or []
    profiles_data = load_json_file(profiles_file) or []
    
    # Create lookup dictionaries
    labels_dict = {item['pair_id']: item for item in labels_data}
    jobs_dict = {item['id']: item for item in jobs_data}
    profiles_dict = {item['profile_id']: item for item in profiles_data}
    
    for pair in pairs_data:
        pair_id = pair.get('pair_id')
        profile_id = pair.get('profile_id')
        job_id = pair.get('job_id')
        
        if not all([pair_id, profile_id, job_id]):
            continue
        
        label = labels_dict.get(pair_id)
        job = jobs_dict.get(job_id)
        profile = profiles_dict.get(profile_id)
        
        if not all([label, job, profile]):
            continue
        
        # Build resume text from profile
        resume_text = (
            f"Candidate: {', '.join(profile.get('roles', []))}\n"
            f"Experience: {profile.get('experience_years', 0)} years\n"
            f"Seniority: {profile.get('seniority', '')}\n"
            f"Primary Skills: {', '.join(profile.get('skills_primary', []))}\n"
            f"Secondary Skills: {', '.join(profile.get('skills_secondary', []))}\n"
            f"Domains: {', '.join(profile.get('domains', []))}\n"
            f"Career Intent: {profile.get('career_intent', '')}"
        )
        
        # Build job description text
        jd_text = (
            f"Title: {job.get('title', '')}\n"
            f"Company: {job.get('company', '')}\n"
            f"Location: {job.get('location', '')}\n"
            f"Description: {job.get('description', '')}\n"
            f"Seniority: {job.get('seniority_level', '')}\n"
            f"Function: {job.get('job_function', '')}"
        )
        
        # Build feedback from label
        composite_score = label.get('composite', 0)
        matches = label.get('matches', [])
        gaps = label.get('gaps', [])
        
        feedback = (
            f"**Match Score:** {composite_score}/100\n\n"
            f"**Strengths:** {', '.join(matches) if matches else 'N/A'}\n\n"
            f"**Gaps:** {', '.join(gaps) if gaps else 'N/A'}\n\n"
            f"**Recommendation:** "
        )
        
        if composite_score >= 80:
            feedback += (
                "Strong match. Tailor the resume to emphasize the matching skills and quantify achievements. "
                "Ensure ATS-friendly formatting and align the summary with the job requirements."
            )
        elif composite_score >= 60:
            feedback += (
                "Moderate match. Highlight transferable skills and address the identified gaps. "
                "Consider additional training or certifications in the missing areas."
            )
        else:
            feedback += (
                "Weak match. The candidate's profile doesn't align well with this role. "
                "Consider targeting positions that better match the current skill set, or invest in upskilling."
            )
        
        user_msg = (
            f"Analyze this resume against the job description and provide detailed HR feedback.\n\n"
            f"JOB DESCRIPTION:\n{clean_text(jd_text)}\n\n"
            f"RESUME:\n{clean_text(resume_text)}"
        )
        
        pairs.append({
            'type': 'job_match',
            'user': user_msg,
            'assistant': clean_text(feedback)
        })
    
    print(f"   ✅ Extracted {len(pairs)} pairs")
    return pairs

def process_ai_job_searcher():
    """Process ai-job-searcher dataset (English AND German for German job market)"""
    print("📦 Processing ai-job-searcher (English + German)...")
    ds_path = "./datasets/ai-job-searcher"
    pairs = []
    
    # Process both English and German datasets
    languages = {
        'en': os.path.join(ds_path, 'data', 'train_en.jsonl'),
        'de': os.path.join(ds_path, 'data', 'train_de.jsonl')
    }
    
    for lang, filepath in languages.items():
        if not os.path.exists(filepath):
            print(f"   ⚠️  {lang.upper()} dataset not found")
            continue
        
        lang_count = 0
        try:
            with open(filepath, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue
                    data = json.loads(line)
                    
                    if 'messages' not in data or len(data['messages']) < 3:
                        continue
                    
                    # Extract user and assistant messages
                    user_msg = ""
                    assistant_msg = ""
                    
                    for msg in data['messages']:
                        if msg['role'] == 'user':
                            user_msg = msg['content']
                        elif msg['role'] == 'assistant':
                            assistant_msg = msg['content']
                    
                    if user_msg and assistant_msg:
                        pairs.append({
                            'type': f'career_advice_{lang}',
                            'user': clean_text(user_msg),
                            'assistant': clean_text(assistant_msg)
                        })
                        lang_count += 1
        except Exception as e:
            print(f"   ⚠️  Error processing {lang.upper()} file: {e}")
        
        print(f"   ✅ Extracted {lang_count} {lang.upper()} pairs")
    
    return pairs

def format_to_chatml(pair):
    """Convert a pair to ChatML JSONL format"""
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": pair['user']},
            {"role": "assistant", "content": pair['assistant']}
        ]
    }

def main():
    print("🚀 Starting data cleaning and formatting...\n")
    
    # Process all datasets
    all_pairs = []
    all_pairs.extend(process_resume_score_details())
    all_pairs.extend(process_role_radar())
    all_pairs.extend(process_ai_job_searcher())
    
    print(f"\n📊 Total raw pairs extracted: {len(all_pairs)}")
    
    # Convert to ChatML format
    chatml_data = []
    skipped = 0
    
    for pair in all_pairs:
        try:
            formatted = format_to_chatml(pair)
            # Validate
            if (formatted['messages'][1]['content'] and 
                formatted['messages'][2]['content'] and
                len(formatted['messages'][2]['content']) > 50):
                chatml_data.append(formatted)
            else:
                skipped += 1
        except Exception as e:
            skipped += 1
    
    print(f"✅ Valid ChatML samples: {len(chatml_data)}")
    print(f"⚠️  Skipped (too short/invalid): {skipped}")
    
    # Shuffle and split
    random.shuffle(chatml_data)
    val_size = int(len(chatml_data) * VAL_SPLIT)
    val_data = chatml_data[:val_size]
    train_data = chatml_data[val_size:]
    
    # Write to files
    with open(OUTPUT_TRAIN, 'w') as f:
        for item in train_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    with open(OUTPUT_VAL, 'w') as f:
        for item in val_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f"\n💾 Saved:")
    print(f"   Training set: {OUTPUT_TRAIN} ({len(train_data)} samples)")
    print(f"   Validation set: {OUTPUT_VAL} ({len(val_data)} samples)")
    
    # Show sample
    if train_data:
        print(f"\n📝 Sample training entry:")
        print(json.dumps(train_data[0], indent=2, ensure_ascii=False)[:2000])

if __name__ == "__main__":
    main()
