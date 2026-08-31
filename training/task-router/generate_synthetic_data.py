import json
import random
import os
from typing import List, Dict, Tuple

def generate_synthetic_data() -> List[Dict[str, str]]:
    """Generates synthetic training data for task routing."""
    data = []

    doc_reasoning_templates = [
        "Summarize the key findings from the {unit} inspection report",
        "What are the recommendations in the last turnaround planning document for {unit}?",
        "Compare the maintenance schedules of {unit1} and {unit2}",
        "Analyze the trend in {resource} consumption over the last quarter",
        "Draft an executive summary for the monthly {facility} performance report",
        "Extract all safety incidents from the {year} annual report",
        "What were the root causes identified in the {incident} investigation?",
        "Generate a timeline of events from the shift handover log",
        "Highlight the critical action items from the morning production meeting",
        "Cross-reference the daily yield reports for inconsistencies",
        "Summarize the feedback from the operator training session",
        "What is the status of the action items from the last hazard review?",
        "Consolidate the weekly maintenance reports into a single summary",
        "Extract the performance metrics from the plant manager's update",
        "Provide a briefing on the recent equipment failure analysis",
        "What are the key takeaways from the environmental audit report?",
        "Summarize the changes proposed in the new operating procedure for {unit}",
        "Identify the recurring issues mentioned in the operator logs",
        "Outline the steps taken during the emergency shutdown procedure",
        "What were the conclusions of the material compatibility study?"
    ]

    code_sandbox_templates = [
        "Calculate the heat duty for the {equipment} given inlet temp {temp}°C",
        "Write a Python script to optimize the {feed} blend ratio for maximum GRM",
        "Compute the pressure drop across the {vessel} using Ergun equation",
        "Simulate the {column} with {stages} theoretical stages",
        "Calculate API gravity and sulfur content for the {crude} crude blend",
        "Write a script to model the kinetics of the {reaction} reaction",
        "Estimate the pump head required for the {fluid} transfer line",
        "Calculate the LMTD for the {exchanger} network",
        "Determine the sizing for the safety relief valve on the {vessel}",
        "Simulate the temperature profile in the {reactor} catalyst bed",
        "Develop a mass balance model for the {unit} unit",
        "Calculate the dew point of the {gas} gas stream",
        "Write a function to estimate the friction factor in a {pipe} pipe",
        "Compute the NPSH available for the {pump}",
        "Model the phase equilibrium for the {system} system",
        "Calculate the compressor power required to compress {gas} to {pressure} bar",
        "Estimate the thermal efficiency of the {furnace}",
        "Write a script to analyze the vibration data from the {compressor}",
        "Calculate the residence time in the {vessel}",
        "Simulate the dynamic response of the {control_loop} control loop"
    ]

    vision_schematic_templates = [
        "Identify all {valve_type} valves in this P&ID drawing",
        "What instruments are connected to the {vessel} in this diagram?",
        "List all safety relief valves shown in this piping schematic",
        "Trace the flow path from the {source} to the {destination}",
        "Identify the interlock logic shown in this cause-and-effect diagram",
        "Extract the pipe sizes and materials from this isometric drawing",
        "Locate the {equipment} in the plot plan",
        "Identify the control loops associated with the {unit}",
        "What is the tag number of the {instrument} shown here?",
        "Find all the tie-in points in this process flow diagram",
        "Verify if the P&ID matches the 3D model for the {system}",
        "Extract the design conditions from the equipment data sheet",
        "Identify the hazardous area classifications in this layout",
        "Trace the electrical routing for the {motor}",
        "List all the nozzles on the {vessel} detailed drawing",
        "Identify the instrument air connections in this schematic",
        "What type of flow meter is installed on the {line} line?",
        "Find the bypass valve around the {equipment}",
        "Identify the isolation valves for the {system} maintenance",
        "Trace the cooling water supply and return lines for the {exchanger}"
    ]

    rag_standards_templates = [
        "What does OISD-{number} say about fire protection for petroleum depots?",
        "List the PNGRB regulations for {topic} integrity management",
        "What are the IS {number} requirements for unfired pressure vessels?",
        "Explain the API {number} inspection interval requirements",
        "What safety distances does OISD-{number} specify for LPG storage?",
        "What are the OSHA requirements for {topic}?",
        "Summarize the NFPA {number} guidelines for {hazard}",
        "What is the permissible exposure limit for {chemical} according to ACGIH?",
        "List the EPA regulations concerning {emission} emissions",
        "What are the ASME BPVC Section {section} requirements for {component}?",
        "Explain the ISO {number} standard for {system}",
        "What are the ATEX directive requirements for {equipment}?",
        "Summarize the IEC {number} standard for {instrument}",
        "What does API RP {number} recommend for {procedure}?",
        "List the NACE standards for {material} in sour service",
        "What are the guidelines for {topic} as per OISD-STD-{number}?",
        "Explain the requirements for {system} in the latest PESO regulations",
        "What are the inspection criteria for {equipment} under API {number}?",
        "Summarize the testing procedures in ASTM {standard}",
        "What are the best practices for {activity} according to CCPS?"
    ]

    fillers = {
        "unit": ["crude distillation unit", "vacuum distillation unit", "fluid catalytic cracker", "delayed coker", "hydrocracker"],
        "unit1": ["CDU-1", "VDU-1", "FCCU", "DCU", "HCU"],
        "unit2": ["CDU-2", "VDU-2", "SRU", "ARU", "DHT"],
        "resource": ["hydrogen", "fuel gas", "steam", "electricity", "cooling water"],
        "facility": ["refinery", "petrochemical plant", "tank farm", "utilities", "offsites"],
        "year": ["2022", "2023", "2024", "2025"],
        "incident": ["pump seal failure", "compressor trip", "furnace tube leak", "heat exchanger fouling", "valve passing"],
        "equipment": ["crude preheater", "reboiler", "condenser", "feed pump", "recycle gas compressor"],
        "temp": ["200", "250", "300", "350", "400"],
        "feed": ["Arab Light", "Basrah Heavy", "Urals", "WTI", "Brent"],
        "vessel": ["reactor bed", "separator", "accumulator", "stripper", "absorber"],
        "column": ["distillation column", "debutanizer", "depropanizer", "deethanizer", "splitter"],
        "stages": ["20", "30", "40", "50", "60"],
        "crude": ["Bombay High", "Kuwait Export", "Murban", "Oman", "Das Blend"],
        "reaction": ["hydrodesulfurization", "catalytic cracking", "isomerization", "reforming", "alkylation"],
        "fluid": ["naphtha", "gas oil", "residue", "LPG", "kerosene"],
        "exchanger": ["preheat train", "overhead condenser", "bottoms cooler", "feed/effluent exchanger"],
        "gas": ["hydrogen", "methane", "ethane", "propane", "butane"],
        "pipe": ["carbon steel", "stainless steel", "alloy", "galvanized", "PVC"],
        "pump": ["centrifugal pump", "positive displacement pump", "rotary pump", "gear pump"],
        "system": ["amine treating", "sour water stripping", "sulfur recovery", "flare system"],
        "pressure": ["10", "20", "50", "100", "150"],
        "furnace": ["crude heater", "vacuum heater", "reformer heater", "coker heater"],
        "compressor": ["make-up gas compressor", "recycle gas compressor", "wet gas compressor", "refrigeration compressor"],
        "control_loop": ["level control", "pressure control", "temperature control", "flow control"],
        "valve_type": ["control", "isolation", "check", "relief", "butterfly"],
        "source": ["crude tank", "feed drum", "storage sphere", "pipeline"],
        "destination": ["atmospheric distillation column", "reactor", "separator", "product tank"],
        "instrument": ["pressure transmitter", "temperature sensor", "flow meter", "level indicator"],
        "motor": ["pump motor", "compressor motor", "fan motor", "mixer motor"],
        "line": ["feed line", "product line", "reflux line", "pump-around line"],
        "number": ["116", "117", "118", "119", "120", "510", "570", "653", "2825", "3183"],
        "topic": ["pipeline", "storage tank", "pressure vessel", "relief system", "fire protection"],
        "hazard": ["flammable liquid", "combustible dust", "toxic gas", "reactive chemical"],
        "chemical": ["benzene", "H2S", "ammonia", "sulfuric acid", "caustic"],
        "emission": ["SOx", "NOx", "VOC", "PM", "CO"],
        "section": ["VIII", "I", "II", "V", "IX"],
        "component": ["boiler", "heat exchanger", "piping", "valve"],
        "procedure": ["welding", "NDT", "pressure testing", "commissioning"],
        "material": ["carbon steel", "stainless steel", "duplex", "inconel"],
        "activity": ["hot work", "confined space entry", "LOTO", "lifting"],
        "standard": ["D86", "D93", "D445", "D1298"]
    }

    categories = {
        0: {"name": "DOC_REASONING", "templates": doc_reasoning_templates},
        1: {"name": "CODE_SANDBOX", "templates": code_sandbox_templates},
        2: {"name": "VISION_SCHEMATIC", "templates": vision_schematic_templates},
        3: {"name": "RAG_STANDARDS", "templates": rag_standards_templates}
    }

    for cat_id, cat_info in categories.items():
        templates = cat_info["templates"]
        cat_data = []
        for _ in range(250):
            template = random.choice(templates)
            
            # format the template by replacing {key} with a random choice from fillers[key]
            kwargs = {}
            import string
            formatter = string.Formatter()
            for _, field_name, _, _ in formatter.parse(template):
                if field_name:
                    kwargs[field_name] = random.choice(fillers[field_name])
                    
            text = template.format(**kwargs)
            cat_data.append({"text": text, "label": cat_info["name"], "category_id": cat_id})
        
        data.extend(cat_data)
        
    random.shuffle(data)
    return data

def save_data(data: List[Dict[str, str]], base_path: str):
    """Saves the data to JSONL files with an 80/20 train/val split."""
    os.makedirs(base_path, exist_ok=True)
    
    split_idx = int(len(data) * 0.8)
    train_data = data[:split_idx]
    val_data = data[split_idx:]
    
    train_path = os.path.join(base_path, "train.jsonl")
    val_path = os.path.join(base_path, "val.jsonl")
    
    with open(train_path, 'w') as f:
        for item in train_data:
            f.write(json.dumps(item) + '\n')
            
    with open(val_path, 'w') as f:
        for item in val_data:
            f.write(json.dumps(item) + '\n')
            
    print(f"Saved {len(train_data)} training examples to {train_path}")
    print(f"Saved {len(val_data)} validation examples to {val_path}")

if __name__ == "__main__":
    random.seed(42)
    synthetic_data = generate_synthetic_data()
    save_dir = os.path.dirname(os.path.abspath(__file__))
    save_data(synthetic_data, save_dir)
