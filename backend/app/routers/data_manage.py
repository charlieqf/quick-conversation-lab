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
        "subtitle": "子宫内膜异位症保守治疗：达芙通与唯散宁方案比较",
        "description": "针对保守治疗的子宫内膜异位症患者，比较达芙通与唯散宁在疼痛缓解、月经规律性、生长发育及不规则出血方面的优势，指导医生优化用药选择。",
        "tags": ["Endometriosis", "Dysmenorrhea", "Dydrogesterone", "Dienogest", "Conservative Treatment", "Patient Education", "Adverse Reactions", "HPO Axis", "Bone Density", "Fertility Preservation", "Drug Comparison", "妇科", "痛经", "子宫内膜异位症", "达芙通", "唯散宁"],
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
        "knowledge_points": """### 1. 痛经与子宫内膜异位症概述
*   **痛经流行病学与影响**：育龄期女性痛经患病率16%～91%，2%～29%出现剧烈疼痛。严重影响女性生活和工作质量（如缺席学习/工作21%～34%，缺席社交/体育活动35%～57%）。疼痛强度与工作/学习不良影响呈正相关。
*   **原发性痛经**：青春期多见，初潮后1～2年内发病。特点是经期前或间期耻骨上周期性痉挛性疼痛，持续8～72h，常伴恶心、呕吐、头晕、头痛、腰痛等症状。妇科检查无异常，无盆腔器质性病变。
*   **继发性痛经**：由于盆腔病理性疾病引起，最常见病因是子宫内膜异位症（约85%患者有痛经），其次是子宫腺肌症（30.0%～77.8%患者有痛经）。疼痛不局限于经期，可在初潮后任何时间发病，月经周期疼痛发作时间或强度改变，可有非周期性或慢性疼痛，亦可有性交疼痛史。
*   **子宫内膜异位症（内异症）**：妇科领域的“良性癌”，兼具恶性生物学行为，尚无根治方法。术后2年复发率21.5%，5年复发率高达40%～50%。应被视为慢性疾病，需要长期管理至绝经或计划妊娠。SOGC指南提出，痛经治疗不应依赖于确诊。

### 2. 地诺孕素 (Dienogest) 机制、适应症、用法用量与特点
*   **作用机制**：
    *   **化学结构**：第4代选择性高效孕激素，同时具有19-去甲睾酮衍生物和孕酮衍生物特性。其17α位乙炔基被氰甲基取代，与肝脏蛋白（如细胞色素P450）相互作用小。
    *   **中枢作用**：中度抑制下丘脑-垂体-卵巢（HPO）轴，下调卵泡刺激素（FSH）和黄体生成素（LH）分泌，进而抑制排卵，降低体循环中雌激素水平。维持雌激素在“治疗窗”（30～50 ng/L），既抑制病灶生长又不引起围绝经期症状和骨质流失。
    *   **外周作用**：抑制芳香酶、环氧合酶2（COX-2）及前列腺素E2（PGE2）表达，抑制卵泡发育，降低病灶局部雌激素。具有抗增殖、促凋亡（抑制细胞周期蛋白D1、诱导自噬）、促进子宫内膜转化（蜕膜化萎缩，诱导子宫内膜转化的能力高于地屈孕酮）、抗炎（阻断炎性因子、改善腹腔微环境）、抗血管生成、抗神经纤维生长作用。
*   **适应症**：治疗子宫内膜异位症。
*   **用法用量**：口服，每日一片（2mg），不间断，最好每天同一时间服用。可于月经周期的任意一天开始。在治疗前需停用任何激素避孕方法，如需避孕，应使用非激素避孕法。
*   **药代动力学**：口服吸收完全且迅速（绝对生物利用度约95%），约1.5h达血药浓度峰值；血浆半衰期6.5～12h；在体内无蓄积效应。
*   **指南推荐**：多国内异症指南/共识（WES、加拿大、韩国、ESHRE、英国、美国）将地诺孕素推荐为内异症经验性治疗和术后管理的一线或A级用药。

### 3. 地诺孕素 (Dienogest) 疗效
*   **疼痛缓解**：显著优于安慰剂（VAS评分减少24.54mm），与GnRH-a（醋酸亮丙瑞林）相当（VAS评分下降47.5mm vs 46.0mm），起效快（4周内40%疼痛缓解）。缓解痛经、性交痛、盆腔痛、盆腔压痛等症状。
*   **病灶缩小**：有效缩小内异症病灶，治疗24周后rAFS评分降低7.8分，超过80%患者中未检测到或仅检测到轻度内异症。有效缩小深部浸润型内异症病灶和术后再复发病灶。
*   **预防复发**：术后连续使用24个月复发率0%（vs 期待疗法24%）；术后连续使用5年累积复发率仅4%（vs 不使用药物69%）。显著减少深部浸润型内异症术后疼痛再发。

### 4. 地诺孕素 (Dienogest) 安全性与不良反应
*   **出血模式改变**：最常见不良反应，尤其在治疗开始后第1个月。表现为治疗初期的阴道不规则出血（发生率可达75%），随着用药时间延长逐渐减少，部分患者最终出现闭经（中国人群闭经率17.6%）。不规则出血是因连续不间断使用单一孕激素类药物，没有规律的孕激素撤退，引发的孕激素突破性出血，通常无法通过停药或加量根本解决。闭经无需治疗，停药后4～6周月经可恢复正常。
*   **HPO轴与骨密度**：中度抑制HPO轴，维持体内雌激素处于治疗窗内，不增加潮热、盗汗、骨质丢失等不良反应。治疗24周期间骨密度未降低。青少年患者应用1年后腰椎骨密度轻微降低，大部分停药后6个月内恢复，尚不明确其临床意义，也无证据表明会增加骨折风险。
*   **代谢影响**：高剂量（20mg/天）和长期使用5年研究结果显示，对血脂、糖代谢、凝血溶血系统、甲状腺参数、肾上腺参数、结合蛋白、血常规等参数无临床意义上的影响。
*   **乳腺**：高剂量治疗24周后，对乳腺厚度、乳腺导管直径和乳晕皮下脂肪层厚度无不良影响。
*   **体重**：未发生改变或仅轻微增加。
*   **VTE风险**：口服单孕激素（避孕用途）与VTE风险增加无关。地诺孕素多项临床研究未见发生VTE。
*   **情绪改变**：少部分患者可能出现头痛、抑郁、失眠、紧张、乏力、性欲减退等，大多可在停药后恢复正常。VIPOS研究中地诺孕素组抑郁发生率为35.7/10000妇女年，发生率与其他治疗药物无差异。
*   **禁忌**：活动性静脉血栓栓塞疾病；当前或既往动脉及心血管疾病；出现血管病变的糖尿病；当前或既往肝功能值未恢复正常的重度肝病；当前或既往肝肿瘤；已知或疑似性激素依赖性恶性肿瘤；原因不明的阴道出血；对活性物质或辅料过敏者。

### 5. 地屈孕酮 (Dydrogesterone) 机制、适应症、用法用量与特点
*   **作用机制**：最接近天然的孕激素，无雌激素、雄激素、糖皮质激素活性。在治疗剂量下不抑制HPO轴。
*   **适应症**：地屈孕酮可用于治疗内源性孕酮不足引起的疾病，如：痛经、子宫内膜异位症、继发性闭经、月经周期不规则、功能失调性子宫出血、经前期综合征、孕激素缺乏所致先兆性流产或习惯性流产、黄体不足所致不孕症；以及用于辅助生殖技术中的黄体支持。
*   **用法用量**：
    *   **痛经**：每日2次，每次口服地屈孕酮1片（10mg），月经周期的第5-25天。
    *   **子宫内膜异位症**：每日2-3次，每次口服地屈孕酮1片（10mg），月经周期的第5-25天。
*   **特点**：治疗剂量下不抑制HPO轴，有助于青春期女性建立正常的HPO轴，不影响青春期内异症患者卵巢功能的建立和骨骼发育。是单孕激素类药物，无雌激素类作用，不会增加深部浸润型内异症（DIE）风险。静脉血栓风险低于复方口服避孕药（COC）。

### 6. 地屈孕酮 (Dydrogesterone) 疗效
*   **疼痛缓解**：显著改善痛经的疼痛症状，使用地屈孕酮从基线到第5周期的总痛经评分平均下降1.84分，且在第2个月经周期时和之后显著降低（p<0.001）。与布洛芬相比，疼痛缓解/消失更优（地屈孕酮疼痛缓解率100% vs 布洛芬26.67%；疼痛消失率86.67% vs 布洛芬0%）。显著改善慢性盆腔疼痛和痛经（NRS评分在6个月时分别降低56%和57%）。显著减少痛经患者止痛药用量（治疗各时期后与治疗前相比，患者止痛药片数均明显下降，P<0.01），停药后3个月未见明显反弹。显著降低镇痛药使用天数（第1-6周期期间降低82%）。
*   **月经周期调节**：治疗痛经的同时可以规律月经周期和经期长度，减少月经量。治疗3个月后月经周期天数从35.6天缩短至29.5天（P<0.05），经期长度从6.3天缩短至5.8天（P<0.05），月经量从59.9mL减少至54.9mL（P<0.05）。达芙通®5-25天用药方案可使患者月经规律，保持稳定。
*   **生活质量**：显著改善育龄期患者治疗期间的生活质量，包括健康认知、心理健康、疼痛、生理功能、角色功能和社会功能等方面均有显著改善（增幅27%～68%）。
*   **囊肿体积**：有效阻止子宫内膜异位囊肿体积增加，治疗至第5周期结束，50%患者子宫内膜异位囊肿体积减小，25%未发生变化。有助于延缓青少年内异症患者疾病进展，保护未来生育力。
*   **妊娠率**：术后使用达芙通®一年妊娠率增加56%，达68.6%（P<0.05）。中国内异症指南（第三版）推荐有生育需求的患者使用达芙通。

### 7. 地屈孕酮 (Dydrogesterone) 安全性与不良反应
*   **HPO轴与骨密度**：治疗剂量下不抑制HPO轴，不影响青春期女性卵巢功能的建立和骨骼发育，不会造成骨密度丢失和抑郁等副作用。
*   **出血模式改变**：达芙通®5-25天用药方案，能够给内膜一个规律的脱落和修复时间，从而让患者用药期间也拥有规律的月经，降低不规则出血发生率。
*   **VTE风险**：地屈孕酮是单孕激素类药物，无雌激素类作用，不会增加DIE风险。静脉血栓风险低于COC（地屈孕酮（孕烷衍生物）IRR 0.9 vs COC IRR 2.92-6.61）。
*   **其他不良反应**：临床试验中接受地屈孕酮治疗适应症但未使用雌激素的患者报告的最常见不良反应是阴道出血、子宫出血、乳房疼痛/敏感、恶心、呕吐、腹痛、偏头痛/头痛。

### 8. 其他治疗方案比较
*   **复方口服避孕药（COC）**：会抑制HPO轴，影响青春期女性的骨骼发育（荟萃分析证实，使用COC 12个月和24个月均会显著降低青春期女性的骨密度）。与NSAIDs同时使用可进一步增加静脉血栓风险（高危激素避孕药和任何非甾体抗炎药同时使用，IRR暴增至50.6）。COC尚无治疗内异症的适应症，止痛和缩病灶的疗效缺乏确切或大样本高质量临床循证依据。既往使用COC治疗重度原发性痛经的女性更常被诊断为内异症，尤其是DIE（内异症OR 5.6，DIE OR 16.2）。
*   **非甾体类抗炎药（NSAIDs）**：可以缓解疼痛但不能延缓疾病进展。频繁使用与抑制排卵、胃溃疡、心血管疾病风险相关。滥用可诱发肝肾损伤、嗜睡、头晕、头痛、视力下降、耳鸣、皮疹等不良反应。现有证据未见在缓解内异症症状上相比安慰剂有更多获益。
*   **中成药（桂枝茯苓胶囊）**：成分温和，见效较慢，治疗效果欠佳。与桂枝茯苓胶囊组比较，地屈孕酮组治疗总有效率明显更高（96.36% vs 81.82%，P＜0.05）。较桂枝茯苓胶囊，地屈孕酮在降低VAS评分、改善CMSS的严重程度、持续时间评分的疗效明显更优。地屈孕酮还具有规律月经的额外获益，而桂枝茯苓胶囊无。
*   **促性腺激素释放激素激动剂（GnRH-a）**：可引起雌激素缺乏症状（潮热、阴道干燥、头痛、性欲减退）以及骨质流失。指南及研究推荐仅用于18岁以上人群，使用3～6个月。

### 9. 子宫内膜异位症诊治指南（第三版）要点
*   **临床诊断依据**：具有1种或多种症状（痛经影响日常活动、慢性盆腔痛、性交痛、与月经周期相关的排便痛/尿痛、伴以上症状的不孕）。妇科体征（子宫后倾固定、附件可扪及囊性肿块、阴道后穹隆/直肠子宫陷凹/宫骶韧带痛性结节、紫蓝色结节）。影像学检查（首选经阴道超声，MRI评估累及肠/膀胱/输尿管的深部内异症）。生物标志物（CA125水平升高）。
*   **手术诊断与分期**：腹腔镜手术是内异症通常的手术诊断方法和金标准。ASRM分期（Ⅰ期1～5分，Ⅱ期6～15分，Ⅲ期16～40分，Ⅳ期＞40分）。
*   **治疗原则**：内异症无法治愈，应最大化药物治疗，避免重复手术操作。药物治疗以长期坚持为目标，选择疗效好、耐受性好的药物。未合并不孕且附件包块直径＜4cm者，首选药物治疗；合并不孕或附件包块直径≥4cm者，考虑手术治疗；药物治疗无效可考虑手术治疗。
*   **分年龄阶段管理**：
    *   **青春期内异症**：尽早开启药物治疗，加强长期随访与管理。推荐复方口服避孕药或孕激素类药物（如地诺孕素）。长期使用孕激素需警惕骨质丢失，骨密度未到峰值的青少年患者应慎用GnRH-a。
    *   **育龄期内异症**：根据临床问题（疼痛、囊肿、不孕、DIE、复发）进行综合治疗与长期管理。
    *   **围绝经期内异症**：需警惕恶变风险，积极治疗、长期随访。
*   **合并子宫腺肌病的治疗**：会导致患者症状加重（盆腔疼痛、异常子宫出血）和生育力进一步下降。治疗方案需兼顾内异症合并不孕与子宫腺肌病合并不孕的指南或共识进行综合考虑，首先推荐IVF-ET。无生育需求者可药物治疗（GnRH-a预处理后序贯COC、地诺孕素或放置LNG-IUS）或手术、介入治疗。
*   **患者教育与随访**：患者教育是提高用药依从性、实现长期管理的关键环节。宣教内容包括内异症临床表现、药物作用机制及副作用、术后用药必要性、定期复查必要性、生育年龄长期用药、不孕积极治疗、恶变风险告知、心理支持等。建议每6个月左右随访1次，远期可个体化调整。随诊指标包括妇科检查、彩超、肿瘤标志物、卵巢功能。
*   **内异症预防**：治疗关口前移，早诊断、早发现、早治疗。通过短效COC预防、规范手术操作、尽早临床诊断并药物治疗等措施，减少病灶形成，控制疾病进展，避免或推迟手术。""",
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
*   **扣分项**：知识点错误、混淆或不清晰；无法有效回答客户提出的专业问题。

**评分说明**：0（未展现）；1分-5分（学习阶段）；6分-8分（应用阶段）；9分-10分（精通阶段）。""",
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

@router.get("/scenarios/{scenario_id}", response_model=ScenarioRead)
def get_scenario(scenario_id: str, db: Session = Depends(get_db)):
    db_obj = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return db_obj

@router.put("/scenarios/{scenario_id}", response_model=ScenarioRead)
def update_scenario(scenario_id: str, scenario: ScenarioCreate, db: Session = Depends(get_db)):
    # ... existing code ...
    db_obj = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    # Update fields
    db_obj.title = scenario.title
    db_obj.subtitle = scenario.subtitle
    db_obj.description = scenario.description
    db_obj.tags = scenario.tags
    db_obj.theme = scenario.theme
    db_obj.script_content = scenario.scriptContent
    db_obj.workflow = scenario.workflow
    db_obj.knowledge_points = scenario.knowledgePoints
    db_obj.scoring_criteria = scenario.scoringCriteria
    db_obj.scoring_dimensions = scenario.scoringDimensions
    db_obj.generation_prompt = scenario.generationPrompt
    
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.delete("/scenarios/{scenario_id}")
def delete_scenario(scenario_id: str, db: Session = Depends(get_db)):
    # ... existing code ...
    db_obj = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    db.delete(db_obj)
    db.commit()
    return {"status": "success"}

# Roles

@router.get("/roles/{role_id}", response_model=RoleRead)
def get_role(role_id: str, db: Session = Depends(get_db)):
    db_obj = db.query(Role).filter(Role.id == role_id).first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Manual Flattening (same as list)
    p = db_obj.personality or {}
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
        personality=p,
        hostility=p.get('hostility', 50),
        verbosity=p.get('verbosity', 50),
        skepticism=p.get('skepticism', 50)
    )

@router.put("/roles/{role_id}", response_model=RoleRead)
def update_role(role_id: str, role: RoleCreate, db: Session = Depends(get_db)):
    db_obj = db.query(Role).filter(Role.id == role_id).first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Role not found")

    personality_json = {
        "hostility": role.hostility,
        "verbosity": role.verbosity,
        "skepticism": role.skepticism
    }
    
    db_obj.name = role.name
    db_obj.name_cn = role.nameCN
    db_obj.title = role.title
    db_obj.description = role.description
    db_obj.avatar_seed = role.avatarSeed
    db_obj.avatar_url = role.avatarImage
    db_obj.focus_areas = role.focusAreas
    db_obj.personality = personality_json
    db_obj.system_prompt_addon = role.systemPromptAddon
    db_obj.generation_prompt = role.generationPrompt
    
    db.commit()
    db.refresh(db_obj)
    
    # Return mapped
    p = db_obj.personality or {}
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
        personality=p,
        hostility=p.get('hostility', 50),
        verbosity=p.get('verbosity', 50),
        skepticism=p.get('skepticism', 50)
    )

@router.delete("/roles/{role_id}")
def delete_role(role_id: str, db: Session = Depends(get_db)):
    db_obj = db.query(Role).filter(Role.id == role_id).first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Role not found")
    
    db.delete(db_obj)
    db.commit()
    return {"status": "success"}
