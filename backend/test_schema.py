from app.schemas import RoleRead
import json

try:
    r = RoleRead(
        id="1",
        name="Test",
        name_cn="TestCN",
        title="Title",
        description="Desc",
        avatar_seed="seed",
        avatar_url=None,
        focus_areas=["A", "B"],
        personality={"hostility": 10},
        system_prompt_addon="sys",
        generation_prompt="gen",
        last_updated="2024-01-01T00:00:00",
        is_default=True,
        hostility=10,
        verbosity=10,
        skepticism=10
    )
    print("DUMP:", r.model_dump())
    print("JSON:", r.model_dump_json())
    print("Validation Alias Check:", r.nameCN)
except Exception as e:
    print("Error:", e)
