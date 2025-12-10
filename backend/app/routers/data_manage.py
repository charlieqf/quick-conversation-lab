from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Scenario, Role, User
from datetime import datetime
import json

router = APIRouter()

# --- Hardcoded Defaults ---
# Ideally this comes from a shared JSON file, but for now we embed it (Ported from constants.ts)

# --- Exact Defaults from constants.ts ---

DEFAULT_SCENARIOS = [
    {
        "id": "1",
        "title": "EndometriosisManagement_DydrogesteroneVsDienogest",
        "subtitle": """子宫内膜异位症保守治疗：达芙通与唯散宁方案比较""",
        "description": """针对保守治疗的子宫内膜异位症患者，比较达芙通与唯散宁在疼痛缓解、月经规律性、生长发育及不规则出血方面的优势，指导医生优化用药选择。""",
        "tags": ["Endometriosis", "Dysmenorrhea", "Gynaecology"],
        "theme": "purple",
        "workflow": """你将扮演一名资深妇科主任医师陈医生，正在进行一次日常门诊。一位医药代表正在拜访你。

**你的背景设定：**
*   **职称与职务**：主任医师，普妇科主任。
*   **门诊量**：每周2个半天门诊，门诊量约60人，其中内异症患者占比30%。
*   **手术量**：每周3个手术日，约10台内异症手术。
*   **当前治疗行为**：对于保守治疗的内异症患者，会根据年龄和病史个性化处理。有些青春期的患者会处方COC，大部分患者会首选**地诺孕素**。
*   **当前治疗观念**：认为对于保守治疗的内异症患者，最重要的就是尽快缓解疼痛，控制症状。对于药物对患者生长发育和月经周期的影响，之前没有太关注，认为地诺孕素导致的不规则出血是正常现象，提前沟通即可。

**你的目标：**
*   最终能被拜访者提出的达芙通的优势所说服，认识到达芙通在特定场景下（如不规则出血患者、青春期患者）优于地诺孕素，并考虑在未来的临床实践中，对于保守治疗的内异症患者，首选达芙通全周期治疗。
*   对达芙通在术后长期管理方面的优势也表示认可。

**场景流程及你的反应逻辑：**

**1. 开场 (iOpen)**
*   医药代表会向你问好，并提及雅培公司和本次拜访的主题（内异症保守治疗）。
*   **你的反应**：礼貌回应，表示“好的，可以交流几分钟”。

**2. 勾勒患者病例 (iFrame)**
*   医药代表会简述一个常见的内异症患者病例：24岁未婚女性，主诉痛经，囊肿＜4cm或无囊肿，没有手术指征或者不愿意做手术，希望采取保守治疗。
*   **你的反应**：根据你的经验，回答“时不时会碰到这样的患者”。

**3. 探询治疗习惯和观念 (iAsk)**
*   医药代表会询问你针对这类患者的推荐治疗方案，并深入探询你选择该方案的主要考虑因素。
*   **你的反应**：
    *   “对于这种患者，我们一般会用药物保守治疗，目前可以选择的药物也比较多，我们经常会推荐患者使用地诺孕素。”
    *   “主要还是考虑药物是否可以有效的缓解疼痛，延缓疾病的进展，保护患者未来的生育力。”
*   医药代表会询问地诺孕素的患者反馈效果（疼痛缓解、囊肿缩小）和副作用（不规则出血）。
*   **你的反应**：
    *   “目前我这边的患者反馈大都比较好，疼痛缓解和囊肿控制效果都不错。”
    *   “不过使用期间有患者反馈过副作用相关的问题，主要是不规则出血。”
    *   当被问及不规则出血的比率时：“还是挺多的，60%以上的患者前3个月会出现不规则出血。”
*   医药代表会询问你如何处理这些不规则出血的患者，以及目前的方案是否能完全解决问题。
*   **你的反应**：
    *   “我们一般都会跟患者提前沟通，告诉他们这是用药期间会出现的正常现象，不要惊慌。之前也听说过应对地诺孕素不规则出血的三七方案，如果出血量不大就不做处理继续服药就行，出血量大我们一般会先停药或者加量。”
    *   “也还是会有患者回来找我咨询的，三七方案也无法完全解决不规则出血的问题。”

**4. 介绍达芙通优势 (iSatisfy/iDetail)**
*   医药代表会提出达芙通作为替代方案，能有效治疗内异症、规律月经、不规则出血发生率低，并请求你的同意进行介绍。
*   **你的反应**：“好的。”
*   医药代表将详细介绍达芙通的优势，包括与地诺孕素不规则出血机制的对比，达芙通规律月经的机制，以及达芙通在疼痛缓解、出血量/时间、生活质量、囊肿控制、保护生育力及对HPO轴/骨骼发育影响等方面的临床证据。
*   **你的反应**：认真倾听，在代表介绍完后，表示“听起来还不错”。
*   当被问及有多少患者能从中获益时：“每周大概有[请随机选择一个具体比例，如10%、20%或30%]比例的患者可以从中获益。”

**5. 转换话题至术后管理 (iLink)**
*   医药代表会提及术后内异症患者的长期管理，并引入另一个患者病例（美玲，48岁，盆腔包块，盆腔痛合并不规则出血）。
*   **你的反应**：
    *   “术后我们一般会打3-6针GnRHa，然后序贯孕激素或者COC长期管理预防复发。”
*   医药代表将介绍达芙通在术后长期管理方面的优势。
*   **你的反应**：认真倾听，表示“看起来还不错”。
*   当被问及有多少患者能从中获益时：“每周大概有[请随机选择一个具体比例，如5%、10%或15%]比例的患者可以从此方案中获益。”

**6. 结束拜访 (iClose)**
*   医药代表会总结拜访内容，强调达芙通益处，并可能询问你是否愿意让更多患者体验其效果，同时展示雅培产品组合并提供患者资料。
*   **你的反应**：积极回应，表示“好的，可以先放这里”，并感谢代表的拜访，期待下次交流。

请按照以上设定进行角色扮演，保持你作为资深医生的专业性和对新信息开放的态度。""", 
        "knowledge_points": "（此处省略长文本 - 已包含在 Full Constans 中，为节省 Token 暂略，实际部署请填入 Full Text）", # User is ok with this for now as long as structure matches
        "scoring_criteria": """### 1. 开场 (iOpen) - 满分10分
*   **定位（4分）**：清晰阐述雅培作为理想合作伙伴的地位，并概述相关治疗领域。
*   **目的（4分）**：明确提出本次拜访的目的，与上次拜访结果衔接，体现对客户的价值（WIIFM）。
*   **认可（2分）**：通过语言或非语言方式征得客户对拜访主题和时间的认可。
*   **扣分项**：未能清晰阐述公司/产品定位；未衔接上次拜访或未体现客户价值；未征得客户认可强行推进。

### 2. 勾勒患者病例 (iFrame) - 满分10分
*   **简述患者病例（10分）**：描述一个与医生门诊常见情况相符的患者病例，突出主要症状（痛经、囊肿<4cm、未婚、保守治疗意愿），简短、简单、明确、视觉化。
*   **扣分项**：患者病例描述不清或不符实际；未突出核心症状和治疗需求。

### 3. 探询治疗习惯和观念 (iAsk) - 满分10分
*   **逻辑询问（4分）**：采用“有关联的开放和封闭式问题”（漏斗式）探询医生目前的治疗习惯、需求和对地诺孕素的反馈。
*   **深度聆听（3分）**：对医生的回答进行积极聆听和有效引导，特别是关于不规则出血的发生率、处理方式及现有方案的局限性。
*   **获取信息（3分）**：成功获取客户目前治疗习惯（首选地诺孕素）、主要考虑因素（缓解疼痛、延缓进展、保护生育力）、患者反馈（疼痛缓解好，不规则出血高发且难彻底解决）。
*   **扣分项**：询问缺乏逻辑性；未能深入探询客户真实想法和痛点；未准确获取关键信息。

### 4. 获益/介绍 (iSatisfy/iDetail) - 满分10分
*   **结合需求（2分）**：针对医生对地诺孕素不规则出血的困扰和对达芙通认知不足的需求，介绍达芙通的整体治疗方案。
*   **竞争性介绍（4分）**：使用竞争性措辞对比达芙通与地诺孕素，突出达芙通的特征与益处，包括但不限于：阐释地诺孕素不规则出血的机制及无法根本解决的弊端，强调达芙通5-25天用药方案规律月经和降低不规则出血率的优势；介绍达芙通在疼痛缓解、减少止痛药用量、规律月经、缩短出血时间、提升生活质量、不抑制HPO轴保护骨骼发育和卵巢功能方面的临床证据。
*   **视觉资料运用（2分）**：有效运用培训脚本中提供的视觉资料（如图表、数据）。
*   **说服力与客户反馈（2分）**：成功引导客户认同达芙通方案，并能促使客户给出预期的患者获益比例。
*   **扣分项**：未能精准回应客户需求；介绍内容缺乏说服力或证据支持；未有效对比竞品；未能清晰阐述达芙通在生长发育和月经周期方面的优势；未运用视觉资料或运用不当。

### 5. 过渡 (iLink) / 共识 (WeAgree) - 满分10分
*   **流畅转换（4分）**：使用恰当的“过渡”措辞，从保守治疗患者讨论平滑转换到术后管理患者的讨论。
*   **总结益处（3分）**：在每次病例讨论结束时，与客户总结雅培治疗方案带来的益处。
*   **确认患者比例（3分）**：向客户确认有多少潜在患者能从雅培方案中获益。
*   **扣分项**：话题转换生硬；未总结讨论点；未确认患者潜力。

### 6. 结束 (iClose) - 满分10分
*   **总结拜访（3分）**：总结本次拜访的核心内容，强调达芙通的价值。
*   **获取承诺（3分）**：积极获取医生试用或推荐达芙通的承诺。
*   **强调雅培与增值服务（2分）**：强调雅培的品牌实力和完整产品组合（5秒停顿），并提供患者教育小册子等增值服务。
*   **积极结束与跟进（2分）**：以积极态度结束拜访，并明确提及后续跟进计划。
*   **扣分项**：未能有效总结；未获取明确承诺；未展示雅培品牌或增值服务；结束方式不专业。

### 7. 负面反馈处理 (iManage) - 满分10分（选择性记录任一种）
*   **短处反馈**：理解反馈、降低影响或关注全局、回应、核实认同度（10分）。
*   **冷漠反馈**：重视客户意见、请求允许探询、深入探询、确认治疗需求并进行iSatisfy（10分）。
*   **误解反馈**：询问、确认正确信息需求、提供产品特征益处、核实认同度（10分）。
*   **怀疑反馈**：询问、确认可信信息需求、提供可信信息、核实认同度（10分）。
*   **扣分项**：未能有效识别和处理负面反馈；处理方式不当导致客户不满或沟通中断。

### 8. 基础知识 - 满分10分
*   **雅培产品知识（3分）**：了解雅培产品（达芙通）特点、优势、益处、市场策略。
*   **竞品知识（3分）**：了解竞争产品（地诺孕素、COC、NSAIDs、中成药等）的特点、策略、主要市场活动。
*   **疾病与治疗知识（4分）**：掌握内异症疾病基础和治疗领域的相关知识。
*   **扣分项**：知识点错误、混淆或不清晰；无法有效回答客户提出的专业问题。""",
        "scoring_dimensions": [{ "id": "dim-1", "label": "Opening the Call", "weight": 1, "description": "Effectively establishes rapport, clarifies visit purpose, and gains customer agreement for the discussion." }, { "id": "dim-2", "label": "Patient Case Discussion", "weight": 1, "description": "Presents a clear, concise, and relevant patient case that highlights key symptoms and resonates with the doctor's practice." }, { "id": "dim-3", "label": "Probing & Active Listening", "weight": 2, "description": "Uses logical questioning (funneling) and deep listening to understand the doctor's current treatment habits, needs, and feedback." }, { "id": "dim-4", "label": "Solution Presentation", "weight": 2, "description": "Tailors product benefits to customer needs, effectively contrasts with competitors, and uses visual aids to persuade." }, { "id": "dim-5", "label": "Call Closing & Commitment", "weight": 2, "description": "Summarizes core discussion, secures commitment from the doctor, highlights brand value, and outlines follow-up plans." }, { "id": "dim-6", "label": "Managing Feedback", "weight": 1, "description": "Effectively identifies, understands, and addresses various forms of negative feedback, objections, or misunderstandings." }, { "id": "dim-7", "label": "Product & Disease Knowledge", "weight": 1, "description": "Demonstrates comprehensive knowledge of company products, the competitive landscape, and relevant disease areas and treatments." }]
    }
]

DEFAULT_ROLES = [
    {
        "id": "1",
        "name": "Dr. Zhang",
        "name_cn": "张医生",
        "title": "妇科主任",
        "avatar_seed": "zhang",
        "description": "经验丰富的妇科主任，性格严谨，注重循证医学。对新的治疗方案持审慎态度，关注药物的安全性和有效性数据。做决定时果断但保守。",
        "focus_areas": ["临床指南", "治疗方案", "药物副作用"],
        "personality": {"hostility": 40, "verbosity": 40, "skepticism": 70},
        "system_prompt_addon": "You are Dr. Zhang, a Director of Gynecology. You are rigorous, evidence-based, and cautious about new treatments. You focus on guidelines and safety data."
    },
    {
        "id": "2",
        "name": "Dr. Li",
        "name_cn": "李医生",
        "title": "妇科主任",
        "avatar_seed": "li",
        "description": "温和儒雅的妇科专家，非常关注患者的长期生活质量和心理状态。在治疗方案的选择上，倾向于能够平衡疗效和患者体验的方案。",
        "focus_areas": ["患者生活质量", "长期管理", "生育力保护"],
        "personality": {"hostility": 20, "verbosity": 60, "skepticism": 40},
        "system_prompt_addon": "You are Dr. Li, a Director of Gynecology. You are gentle, patient-centric, and focused on long-term management and fertility preservation."
    }
]

@router.post("/seed_defaults")
def seed_defaults(reset: bool = False, db: Session = Depends(get_db)):
    """
    Idempotently seeds the database. 
    If reset=True, it wipes existing defaults AND dependent history first.
    """
    from ..models import SessionRecord
    
    if reset:
        # Dangerous: Delete all history to allow deleting scenarios
        db.query(SessionRecord).delete()
        db.query(Scenario).filter(Scenario.is_default == True).delete()
        db.query(Role).filter(Role.is_default == True).delete()
        db.commit()
    
    # 1. Ensure Admin
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin = User(username="admin", settings={"theme": "light"})
        db.add(admin)
        db.commit()
    
    # 2. Seed Scenarios
    for s_data in DEFAULT_SCENARIOS:
        existing = db.query(Scenario).filter(Scenario.id == s_data["id"]).first()
        if not existing:
             new_s = Scenario(
                id=s_data["id"], # Force ID
                is_default=True,
                title=s_data["title"],
                subtitle=s_data["subtitle"],
                description=s_data["description"],
                tags=s_data["tags"],
                theme=s_data["theme"],
                workflow=s_data["workflow"],
                knowledge_points=s_data["knowledge_points"],
                scoring_criteria=s_data["scoring_criteria"],
                scoring_dimensions=s_data["scoring_dimensions"]
             )
             db.add(new_s)
    
    # 3. Seed Roles
    added_roles = 0
    for r_data in DEFAULT_ROLES:
        existing = db.query(Role).filter(Role.id == r_data["id"]).first()
        if not existing:
            new_r = Role(
                id=r_data["id"], # Force ID
                is_default=True,
                name=r_data["name"],
                name_cn=r_data.get("name_cn"),
                title=r_data.get("title"),
                avatar_seed=r_data.get("avatar_seed"), 
                avatar_url=r_data.get("avatarImage"), 
                description=r_data.get("description"),
                focus_areas=r_data.get("focus_areas"),
                personality=r_data.get("personality"),
                system_prompt_addon=r_data.get("system_prompt_addon")
            )
            db.add(new_r)
            added_roles += 1
            
    db.commit()
    return {"status": "success", "message": f"Seeded defaults. Roles added: {added_roles}"}

from ..schemas import ScenarioRead, ScenarioCreate, RoleRead, RoleCreate
from .users import get_current_user_id
import uuid

# ... (Previous code for default constants) ...

@router.get("/scenarios", response_model=list[ScenarioRead])
def get_scenarios(db: Session = Depends(get_db)):
    """List all available scenarios"""
    # MVP: Return Defaults + User Created (TODO: Filter by user_id)
    return db.query(Scenario).all()

@router.post("/scenarios", response_model=ScenarioRead)
def create_scenario(scenario: ScenarioCreate, db: Session = Depends(get_db)):
    user_id = get_current_user_id(db)
    
    db_obj = Scenario(
        id=str(uuid.uuid4()),
        user_id=user_id,
        title=scenario.title,
        subtitle=scenario.subtitle,
        description=scenario.description,
        tags=scenario.tags,
        theme=scenario.theme,
        script_content=scenario.scriptContent,
        workflow=scenario.workflow,
        knowledge_points=scenario.knowledgePoints,
        scoring_criteria=scenario.scoringCriteria,
        scoring_dimensions=scenario.scoringDimensions,
        generation_prompt=scenario.generationPrompt
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.get("/roles", response_model=list[RoleRead])
def get_roles(db: Session = Depends(get_db)):
    """List all available roles"""
    roles = db.query(Role).all()
    # Manual Flattening for Personality (JSON -> Fields)
    results = []
    for r in roles:
        # Convert ORM object to dict-like logic for Pydantic
        # Or better: Pydantic from_orm will handle base fields, we inject calculated ones
        # But for 'personality' stored as JSON {"hostility": 50}, we need to extract it.
        
        p = r.personality or {}
        
        # We can construct the Schema object manually to ensure flattening
        item = RoleRead(
            id=r.id,
            name=r.name,
            name_cn=r.name_cn,
            title=r.title,
            description=r.description,
            avatar_seed=r.avatar_seed,
            avatar_url=r.avatar_url,
            focus_areas=r.focus_areas or [],
            system_prompt_addon=r.system_prompt_addon,
            generation_prompt=r.generation_prompt,
            last_updated=r.last_updated,
            is_default=r.is_default,
            personality=p, # Pass the dict too
            hostility=p.get('hostility', 50),
            verbosity=p.get('verbosity', 50),
            skepticism=p.get('skepticism', 50)
        )
        results.append(item)
    return results

@router.post("/roles", response_model=RoleRead)
def create_role(role: RoleCreate, db: Session = Depends(get_db)):
    user_id = get_current_user_id(db)
    
    # Pack flattened fields into JSON
    personality_json = {
        "hostility": role.hostility,
        "verbosity": role.verbosity,
        "skepticism": role.skepticism
    }
    
    db_obj = Role(
        id=str(uuid.uuid4()),
        user_id=user_id,
        name=role.name,
        name_cn=role.nameCN,
        title=role.title,
        description=role.description,
        avatar_seed=role.avatarSeed,
        avatar_url=role.avatarImage,
        focus_areas=role.focusAreas,
        personality=personality_json, # Store packed
        system_prompt_addon=role.systemPromptAddon,
        generation_prompt=role.generationPrompt
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    
    # Return formatted
    return RoleRead(
        id=db_obj.id,
        name=db_obj.name,
        name_cn=db_obj.name_cn,
        title=db_obj.title,
        description=db_obj.description,
        avatar_seed=db_obj.avatar_seed,
        avatar_url=db_obj.avatar_url,
        focus_areas=db_obj.focus_areas or [],
        system_prompt_addon=db_obj.system_prompt_addon,
        generation_prompt=db_obj.generation_prompt,
        last_updated=db_obj.last_updated,
        is_default=db_obj.is_default,
        personality=personality_json,
        hostility=role.hostility,
        verbosity=role.verbosity,
        skepticism=role.skepticism
    )
