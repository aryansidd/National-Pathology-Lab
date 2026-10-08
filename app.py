from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import sqlite3, os, io, re, math
from datetime import datetime
import sys, threading, webbrowser, socket
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader

NATIVE_APP=False

CODE_DIR=os.path.dirname(os.path.abspath(__file__))
RESOURCE_DIR=getattr(sys, '_MEIPASS', CODE_DIR)
APP_DIR=(os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'NationalPathologyLab') if getattr(sys, 'frozen', False) else CODE_DIR)
os.makedirs(APP_DIR, exist_ok=True)
os.makedirs(os.path.join(APP_DIR, 'static', 'uploads'), exist_ok=True)
DB=os.path.join(APP_DIR,"lab.db")
app=Flask(__name__, template_folder=os.path.join(RESOURCE_DIR,'templates'))
app.secret_key="national-pathology-change-this"

# Broad starter catalogue. Every installed test gets at least one editable report parameter.
DEFAULT_TESTS=[('CBC / Complete Blood Count', 300, 'Hematology'), ('ESR', 100, 'Hematology'), ('Peripheral Blood Smear', 250, 'Hematology'), ('Reticulocyte Count', 200, 'Hematology'), ('AEC', 150, 'Hematology'), ('Sickling Test', 250, 'Hematology'), ('G6PD', 600, 'Hematology'), ('Hb Electrophoresis', 1200, 'Hematology'), ('Thalassemia Screening', 700, 'Hematology'), ('Bleeding Time (BT)', 100, 'Coagulation'), ('Clotting Time (CT)', 100, 'Coagulation'), ('PT / INR', 350, 'Coagulation'), ('APTT', 350, 'Coagulation'), ('D-Dimer', 700, 'Coagulation'), ('Fibrinogen', 600, 'Coagulation'), ('Blood Group & Rh', 100, 'Immunohematology'), ('Cross Matching', 300, 'Immunohematology'), ('Direct Coombs Test', 500, 'Immunohematology'), ('Indirect Coombs Test', 500, 'Immunohematology'), ('Blood Sugar Fasting (FBS)', 100, 'Biochemistry'), ('Blood Sugar PP (PPBS)', 100, 'Biochemistry'), ('Random Blood Sugar (RBS)', 100, 'Biochemistry'), ('HbA1c', 350, 'Biochemistry'), ('Liver Function Test (LFT)', 450, 'Biochemistry'), ('Kidney/Renal Function Test (KFT/RFT)', 400, 'Biochemistry'), ('Lipid Profile', 400, 'Biochemistry'), ('Serum Calcium', 150, 'Biochemistry'), ('Serum Phosphorus', 150, 'Biochemistry'), ('Serum Magnesium', 250, 'Biochemistry'), ('Serum Uric Acid', 150, 'Biochemistry'), ('Serum Amylase', 350, 'Biochemistry'), ('Serum Lipase', 450, 'Biochemistry'), ('Total Protein', 150, 'Biochemistry'), ('Albumin', 150, 'Biochemistry'), ('Bilirubin Total', 120, 'Biochemistry'), ('Bilirubin Direct', 120, 'Biochemistry'), ('AST / SGOT', 120, 'Biochemistry'), ('ALT / SGPT', 120, 'Biochemistry'), ('Alkaline Phosphatase (ALP)', 150, 'Biochemistry'), ('GGT', 200, 'Biochemistry'), ('LDH', 250, 'Biochemistry'), ('Electrolytes (Na/K/Cl)', 450, 'Biochemistry'), ('Serum Sodium', 150, 'Biochemistry'), ('Serum Potassium', 150, 'Biochemistry'), ('Serum Chloride', 150, 'Biochemistry'), ('Blood Urea', 120, 'Biochemistry'), ('Serum Creatinine', 120, 'Biochemistry'), ('eGFR', 200, 'Biochemistry'), ('BUN', 150, 'Biochemistry'), ('Iron Profile', 500, 'Biochemistry'), ('Serum Iron', 200, 'Biochemistry'), ('TIBC', 250, 'Biochemistry'), ('Ferritin', 500, 'Biochemistry'), ('Vitamin D (25-OH)', 650, 'Vitamins'), ('Vitamin B12', 450, 'Vitamins'), ('Folate', 500, 'Vitamins'), ('Thyroid Profile (T3, T4, TSH)', 450, 'Hormones'), ('TSH', 180, 'Hormones'), ('Free T3', 250, 'Hormones'), ('Free T4', 250, 'Hormones'), ('T3', 180, 'Hormones'), ('T4', 180, 'Hormones'), ('FT3 + FT4 + TSH', 500, 'Hormones'), ('Insulin Fasting', 450, 'Hormones'), ('Cortisol', 500, 'Hormones'), ('Prolactin', 400, 'Hormones'), ('FSH', 400, 'Hormones'), ('LH', 400, 'Hormones'), ('Estradiol (E2)', 500, 'Hormones'), ('Progesterone', 500, 'Hormones'), ('Testosterone', 500, 'Hormones'), ('Free Testosterone', 700, 'Hormones'), ('Beta hCG', 500, 'Hormones'), ('AMH', 1000, 'Hormones'), ('Urine Routine & Microscopy', 150, 'Clinical Pathology'), ('Urine Pregnancy Test', 150, 'Clinical Pathology'), ('Urine Culture & Sensitivity', 600, 'Microbiology'), ('Stool Routine Examination', 200, 'Clinical Pathology'), ('Stool Occult Blood', 200, 'Clinical Pathology'), ('Stool Culture', 600, 'Microbiology'), ('Semen Analysis', 400, 'Clinical Pathology'), ('Dengue NS1 Antigen', 500, 'Serology'), ('Dengue IgG/IgM', 600, 'Serology'), ('Dengue Profile', 900, 'Serology'), ('Malaria Parasite (MP)', 300, 'Serology'), ('Malaria Antigen', 400, 'Serology'), ('Widal Test', 250, 'Serology'), ('Typhidot IgM', 400, 'Serology'), ('Typhidot IgG', 400, 'Serology'), ('CRP', 300, 'Immunology'), ('hs-CRP', 500, 'Immunology'), ('ASO Titre', 250, 'Immunology'), ('RA Factor', 250, 'Immunology'), ('ANA', 700, 'Immunology'), ('Anti-CCP', 900, 'Immunology'), ('HIV 1&2', 500, 'Serology'), ('HBsAg', 400, 'Serology'), ('Anti-HCV', 500, 'Serology'), ('VDRL / RPR', 300, 'Serology'), ('TPHA', 500, 'Serology'), ('HAV IgM', 500, 'Serology'), ('HEV IgM', 500, 'Serology'), ('HBc IgM', 500, 'Serology'), ('Chikungunya IgM', 500, 'Serology'), ('Chikungunya IgG', 500, 'Serology'), ('H. pylori IgG', 500, 'Serology'), ('H. pylori Antigen', 600, 'Clinical Pathology'), ('Blood Culture', 800, 'Microbiology'), ('Pus/Wound Culture', 700, 'Microbiology'), ('Sputum Culture', 700, 'Microbiology'), ('Culture & Sensitivity', 800, 'Microbiology'), ('KOH Mount', 250, 'Microbiology'), ('Gram Stain', 200, 'Microbiology'), ('AFB Stain', 300, 'Microbiology'), ('Pap Smear', 600, 'Cytology'), ('FNAC', 1200, 'Cytology'), ('Cytology Examination', 800, 'Cytology'), ('Histopathology Biopsy', 1500, 'Histopathology'), ('Histopathology Large Specimen', 2500, 'Histopathology'), ('PSA Total', 500, 'Tumor Markers'), ('Free PSA', 600, 'Tumor Markers'), ('CEA', 700, 'Tumor Markers'), ('AFP', 700, 'Tumor Markers'), ('CA-125', 800, 'Tumor Markers'), ('CA 19-9', 800, 'Tumor Markers'), ('CA 15-3', 800, 'Tumor Markers'), ('Urine Microalbumin', 350, 'Renal'), ('Urine Protein 24 Hour', 500, 'Renal'), ('ACR (Albumin/Creatinine Ratio)', 400, 'Renal')]

# Parameter catalogue. Ranges are starter values only and MUST be verified against the lab's method/analyzer/pathologist.
# Each tuple: parameter, unit, male range, female range.
REPORT_CATALOG={
'CBC / Complete Blood Count': [('Hemoglobin','g/dL','13.0 - 17.0','12.0 - 15.5'),('RBC Count','million/µL','4.5 - 5.9','4.1 - 5.1'),('Total WBC Count','/µL','4,000 - 11,000','4,000 - 11,000'),('Platelet Count','lakh/µL','1.5 - 4.5','1.5 - 4.5'),('Hematocrit (PCV)','%','40 - 50','36 - 46'),('MCV','fL','83 - 101','83 - 101'),('MCH','pg','27 - 32','27 - 32'),('MCHC','g/dL','31 - 35','31 - 35'),('Neutrophils','%','40 - 75','40 - 75'),('Lymphocytes','%','20 - 45','20 - 45'),('Monocytes','%','2 - 10','2 - 10'),('Eosinophils','%','1 - 6','1 - 6'),('Basophils','%','0 - 1','0 - 1')],
'ESR': [('ESR','mm/hr','0 - 15','0 - 20')],
'Peripheral Blood Smear': [('RBC Morphology','','Normocytic normochromic','Normocytic normochromic'),('WBC Morphology','','Normal','Normal'),('Platelets','','Adequate','Adequate'),('Parasites','','Absent','Absent')],
'Reticulocyte Count': [('Reticulocyte Count','%','0.5 - 2.5','0.5 - 2.5')],
'AEC': [('Absolute Eosinophil Count','/µL','40 - 400','40 - 400')],
'Sickling Test': [('Sickling Test','','Negative','Negative')],
'G6PD': [('G6PD Activity','U/g Hb','4.6 - 13.5','4.6 - 13.5')],
'Hb Electrophoresis': [('HbA','%','95 - 98','95 - 98'),('HbA2','%','1.5 - 3.5','1.5 - 3.5'),('HbF','%','0 - 2','0 - 2')],
'Thalassemia Screening': [('MCV','fL','83 - 101','83 - 101'),('MCH','pg','27 - 32','27 - 32'),('Mentzer Index','','> 13','> 13')],
'Bleeding Time (BT)': [('Bleeding Time','min','2 - 7','2 - 7')],
'Clotting Time (CT)': [('Clotting Time','min','5 - 11','5 - 11')],
'PT / INR': [('PT','sec','10 - 14','10 - 14'),('INR','','0.8 - 1.2','0.8 - 1.2')],
'APTT': [('APTT','sec','25 - 35','25 - 35')],
'D-Dimer': [('D-Dimer','µg/mL FEU','0 - 0.50','0 - 0.50')],
'Fibrinogen': [('Fibrinogen','mg/dL','200 - 400','200 - 400')],
'Blood Group & Rh': [('ABO Group','','A / B / AB / O','A / B / AB / O'),('Rh Factor','','Positive / Negative','Positive / Negative')],
'Cross Matching': [('Cross Match','','Compatible','Compatible')],
'Direct Coombs Test': [('DAT','','Negative','Negative')],
'Indirect Coombs Test': [('IAT','','Negative','Negative')],
'Blood Sugar Fasting (FBS)': [('Fasting Blood Sugar','mg/dL','70 - 99','70 - 99')],
'Blood Sugar PP (PPBS)': [('Post Prandial Blood Sugar','mg/dL','< 140','< 140')],
'Random Blood Sugar (RBS)': [('Random Blood Sugar','mg/dL','70 - 140','70 - 140')],
'HbA1c': [('HbA1c','%','4.0 - 5.6','4.0 - 5.6')],
'Liver Function Test (LFT)': [('Bilirubin Total','mg/dL','0.2 - 1.2','0.2 - 1.2'),('Bilirubin Direct','mg/dL','0.0 - 0.3','0.0 - 0.3'),('Bilirubin Indirect','mg/dL','0.2 - 0.9','0.2 - 0.9'),('AST / SGOT','U/L','5 - 40','5 - 40'),('ALT / SGPT','U/L','7 - 56','7 - 56'),('Alkaline Phosphatase','U/L','44 - 147','44 - 147'),('GGT','U/L','9 - 48','6 - 42'),('Total Protein','g/dL','6.0 - 8.3','6.0 - 8.3'),('Albumin','g/dL','3.5 - 5.0','3.5 - 5.0'),('Globulin','g/dL','2.0 - 3.5','2.0 - 3.5'),('A/G Ratio','','1.0 - 2.5','1.0 - 2.5')],
'Kidney/Renal Function Test (KFT/RFT)': [('Blood Urea','mg/dL','15 - 45','15 - 45'),('Serum Creatinine','mg/dL','0.7 - 1.3','0.6 - 1.1'),('Uric Acid','mg/dL','3.5 - 7.2','2.6 - 6.0'),('Sodium','mmol/L','135 - 145','135 - 145'),('Potassium','mmol/L','3.5 - 5.1','3.5 - 5.1'),('Chloride','mmol/L','98 - 107','98 - 107'),('eGFR','mL/min/1.73m²','> 60','> 60')],
'Lipid Profile': [('Total Cholesterol','mg/dL','< 200','< 200'),('Triglycerides','mg/dL','< 150','< 150'),('HDL Cholesterol','mg/dL','> 40','> 50'),('LDL Cholesterol','mg/dL','< 100','< 100'),('VLDL','mg/dL','5 - 40','5 - 40')],
'Serum Calcium': [('Calcium','mg/dL','8.5 - 10.5','8.5 - 10.5')],
'Serum Phosphorus': [('Phosphorus','mg/dL','2.5 - 4.5','2.5 - 4.5')],
'Serum Magnesium': [('Magnesium','mg/dL','1.7 - 2.4','1.7 - 2.4')],
'Serum Uric Acid': [('Uric Acid','mg/dL','3.5 - 7.2','2.6 - 6.0')],
'Serum Amylase': [('Amylase','U/L','30 - 110','30 - 110')],
'Serum Lipase': [('Lipase','U/L','13 - 60','13 - 60')],
'Total Protein': [('Total Protein','g/dL','6.0 - 8.3','6.0 - 8.3')],
'Albumin': [('Albumin','g/dL','3.5 - 5.0','3.5 - 5.0')],
'Bilirubin Total': [('Bilirubin Total','mg/dL','0.2 - 1.2','0.2 - 1.2')],
'Bilirubin Direct': [('Bilirubin Direct','mg/dL','0.0 - 0.3','0.0 - 0.3')],
'AST / SGOT': [('AST / SGOT','U/L','5 - 40','5 - 40')],
'ALT / SGPT': [('ALT / SGPT','U/L','7 - 56','7 - 56')],
'Alkaline Phosphatase (ALP)': [('Alkaline Phosphatase','U/L','44 - 147','44 - 147')],
'GGT': [('GGT','U/L','9 - 48','6 - 42')],
'LDH': [('LDH','U/L','140 - 280','140 - 280')],
'Electrolytes (Na/K/Cl)': [('Sodium','mmol/L','135 - 145','135 - 145'),('Potassium','mmol/L','3.5 - 5.1','3.5 - 5.1'),('Chloride','mmol/L','98 - 107','98 - 107')],
'Serum Sodium': [('Sodium','mmol/L','135 - 145','135 - 145')],
'Serum Potassium': [('Potassium','mmol/L','3.5 - 5.1','3.5 - 5.1')],
'Serum Chloride': [('Chloride','mmol/L','98 - 107','98 - 107')],
'Blood Urea': [('Blood Urea','mg/dL','15 - 45','15 - 45')],
'Serum Creatinine': [('Serum Creatinine','mg/dL','0.7 - 1.3','0.6 - 1.1')],
'eGFR': [('eGFR','mL/min/1.73m²','> 60','> 60')],
'BUN': [('BUN','mg/dL','7 - 20','7 - 20')],
'Iron Profile': [('Serum Iron','µg/dL','65 - 175','50 - 170'),('TIBC','µg/dL','240 - 450','240 - 450'),('Ferritin','ng/mL','30 - 400','13 - 150'),('Transferrin Saturation','%','20 - 50','15 - 50')],
'Serum Iron': [('Serum Iron','µg/dL','65 - 175','50 - 170')],
'TIBC': [('TIBC','µg/dL','240 - 450','240 - 450')],
'Ferritin': [('Ferritin','ng/mL','30 - 400','13 - 150')],
'Vitamin D (25-OH)': [('Vitamin D','ng/mL','30 - 100','30 - 100')],
'Vitamin B12': [('Vitamin B12','pg/mL','200 - 900','200 - 900')],
'Folate': [('Folate','ng/mL','4.0 - 20.0','4.0 - 20.0')],
'Thyroid Profile (T3, T4, TSH)': [('T3','ng/mL','0.8 - 2.0','0.8 - 2.0'),('T4','µg/dL','5.0 - 12.0','5.0 - 12.0'),('TSH','µIU/mL','0.4 - 4.0','0.4 - 4.0')],
'TSH': [('TSH','µIU/mL','0.4 - 4.0','0.4 - 4.0')],
'Free T3': [('Free T3','pg/mL','2.0 - 4.4','2.0 - 4.4')],
'Free T4': [('Free T4','ng/dL','0.8 - 1.8','0.8 - 1.8')],
'T3': [('T3','ng/mL','0.8 - 2.0','0.8 - 2.0')],
'T4': [('T4','µg/dL','5.0 - 12.0','5.0 - 12.0')],
'FT3 + FT4 + TSH': [('Free T3','pg/mL','2.0 - 4.4','2.0 - 4.4'),('Free T4','ng/dL','0.8 - 1.8','0.8 - 1.8'),('TSH','µIU/mL','0.4 - 4.0','0.4 - 4.0')],
'Insulin Fasting': [('Fasting Insulin','µIU/mL','2.6 - 24.9','2.6 - 24.9')],
'Cortisol': [('Cortisol','µg/dL','5 - 25','5 - 25')],
'Prolactin': [('Prolactin','ng/mL','4 - 15','4 - 23')],
'FSH': [('FSH','mIU/mL','1.5 - 12.4','follicular 3.5 - 12.5'),('LH','mIU/mL','1.7 - 8.6','follicular 2.4 - 12.6')],
'LH': [('LH','mIU/mL','1.7 - 8.6','follicular 2.4 - 12.6')],
'Estradiol (E2)': [('Estradiol','pg/mL','10 - 40','follicular 20 - 350')],
'Progesterone': [('Progesterone','ng/mL','0.2 - 1.4','follicular 0.1 - 1.5')],
'Testosterone': [('Testosterone','ng/dL','300 - 1000','15 - 70')],
'Free Testosterone': [('Free Testosterone','pg/mL','5 - 25','0.1 - 1.9')],
'Beta hCG': [('Beta hCG','mIU/mL','< 5','< 5 (non-pregnant)')],
'AMH': [('AMH','ng/mL','1.0 - 5.0','0.5 - 6.0')],
'Urine Routine & Microscopy': [('Colour','','Pale Yellow','Pale Yellow'),('Appearance','','Clear','Clear'),('Protein','','Negative','Negative'),('Glucose','','Negative','Negative'),('Ketone','','Negative','Negative'),('Pus Cells','/HPF','0 - 5','0 - 5'),('RBC','/HPF','0 - 2','0 - 2'),('Epithelial Cells','/HPF','Few','Few'),('Bacteria','','Absent','Absent')],
'Urine Pregnancy Test': [('Pregnancy Test','','Negative','Negative')],
'Stool Routine Examination': [('Colour','','Brown','Brown'),('Consistency','','Formed','Formed'),('Occult Blood','','Negative','Negative'),('Ova/Cyst','','Not seen','Not seen'),('Pus Cells','/HPF','0 - 5','0 - 5')],
'Stool Occult Blood': [('Occult Blood','','Negative','Negative')],
'Semen Analysis': [('Volume','mL','1.4 - 6.0','1.4 - 6.0'),('Appearance','','Greyish white','Greyish white'),('Liquefaction','min','< 60','< 60'),('Viscosity','','Normal','Normal'),('pH','','7.2 - 8.0','7.2 - 8.0'),('Sperm Count','million/mL','≥ 16','≥ 16'),('Progressive Motility','%','≥ 30','≥ 30'),('Total Motility','%','≥ 42','≥ 42'),('Normal Morphology','%','≥ 4','≥ 4'),('Pus Cells','/HPF','0 - 5','0 - 5'),('RBC','','Absent','Absent')],
'Dengue NS1 Antigen': [('NS1 Antigen','','Negative','Negative')],
'Dengue IgG/IgM': [('Dengue IgM','','Negative','Negative'),('Dengue IgG','','Negative','Negative')],
'Dengue Profile': [('NS1 Antigen','','Negative','Negative'),('Dengue IgM','','Negative','Negative'),('Dengue IgG','','Negative','Negative')],
'Malaria Parasite (MP)': [('Malarial Parasite','','Not Seen','Not Seen')],
'Malaria Antigen': [('Malaria Antigen','','Negative','Negative')],
'Widal Test': [('S. typhi O titre','','< 1:80','< 1:80'),('S. typhi H titre','','< 1:80','< 1:80'),('S. paratyphi AH titre','','< 1:80','< 1:80'),('S. paratyphi BH titre','','< 1:80','< 1:80')],
'Typhidot IgM': [('Typhidot IgM','','Negative','Negative')],
'Typhidot IgG': [('Typhidot IgG','','Negative','Negative')],
'CRP': [('CRP','mg/L','0 - 5','0 - 5')],
'hs-CRP': [('hs-CRP','mg/L','< 3','< 3')],
'ASO Titre': [('ASO Titre','IU/mL','< 200','< 200')],
'RA Factor': [('RA Factor','IU/mL','< 14','< 14')],
'ANA': [('ANA','','Negative','Negative')],
'Anti-CCP': [('Anti-CCP','U/mL','< 20','< 20')],
'HIV 1&2': [('HIV 1&2','','Non-Reactive','Non-Reactive')],
'HBsAg': [('HBsAg','','Non-Reactive','Non-Reactive')],
'Anti-HCV': [('Anti-HCV','','Non-Reactive','Non-Reactive')],
'VDRL / RPR': [('VDRL / RPR','','Non-Reactive','Non-Reactive')],
'TPHA': [('TPHA','','Non-Reactive','Non-Reactive')],
'HAV IgM': [('HAV IgM','','Negative','Negative')],
'HEV IgM': [('HEV IgM','','Negative','Negative')],
'HBc IgM': [('HBc IgM','','Negative','Negative')],
'Chikungunya IgM': [('Chikungunya IgM','','Negative','Negative')],
'Chikungunya IgG': [('Chikungunya IgG','','Negative','Negative')],
'H. pylori IgG': [('H. pylori IgG','','Negative','Negative')],
'H. pylori Antigen': [('H. pylori Antigen','','Negative','Negative')],
'Blood Culture': [('Culture Result','','No growth / Growth','No growth / Growth')],
'Pus/Wound Culture': [('Culture Result','','No growth / Growth','No growth / Growth'),('Sensitivity','','As per culture','As per culture')],
'Sputum Culture': [('Culture Result','','No growth / Growth','No growth / Growth')],
'Culture & Sensitivity': [('Culture Result','','No growth / Growth','No growth / Growth'),('Sensitivity','','As per culture','As per culture')],
'KOH Mount': [('KOH Mount','','No fungal elements seen','No fungal elements seen')],
'Gram Stain': [('Gram Stain','','No significant organism seen','No significant organism seen')],
'AFB Stain': [('AFB Stain','','Negative','Negative')],
'Pap Smear': [('Cytology Result','','Negative for intraepithelial lesion or malignancy','Negative for intraepithelial lesion or malignancy')],
'FNAC': [('Cytology Result','','See cytology interpretation','See cytology interpretation')],
'Cytology Examination': [('Cytology Result','','See cytology interpretation','See cytology interpretation')],
'Histopathology Biopsy': [('Histopathology Result','','See histopathology diagnosis','See histopathology diagnosis')],
'Histopathology Large Specimen': [('Histopathology Result','','See histopathology diagnosis','See histopathology diagnosis')],
'PSA Total': [('PSA','ng/mL','< 4.0','< 4.0')],
'Free PSA': [('Free PSA','ng/mL','> 0.25','> 0.25')],
'CEA': [('CEA','ng/mL','< 3.0','< 3.0')],
'AFP': [('AFP','ng/mL','< 10','< 10')],
'CA-125': [('CA-125','U/mL','< 35','< 35')],
'CA 19-9': [('CA 19-9','U/mL','< 37','< 37')],
'CA 15-3': [('CA 15-3','U/mL','< 30','< 30')],
'Urine Microalbumin': [('Microalbumin','mg/L','< 30','< 30')],
'Urine Protein 24 Hour': [('Urine Protein 24h','mg/day','< 150','< 150')],
'ACR (Albumin/Creatinine Ratio)': [('ACR','mg/g','< 30','< 30')],
}

# Generic fallback keeps every installed test available in the report editor.
for _name,_,_cat in DEFAULT_TESTS:
    REPORT_CATALOG.setdefault(_name,[('Result','','Method dependent','Method dependent')])


def db():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def init_db():
    c=db()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS settings(id INTEGER PRIMARY KEY CHECK(id=1),lab_name TEXT,address TEXT,phone TEXT,email TEXT,authorized_name TEXT,qualification TEXT,signature_path TEXT,report_base_url TEXT);
    CREATE TABLE IF NOT EXISTS doctors(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,qualification TEXT,phone TEXT);
    CREATE TABLE IF NOT EXISTS tests(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT UNIQUE NOT NULL,price REAL NOT NULL,category TEXT);
    CREATE TABLE IF NOT EXISTS patients(id INTEGER PRIMARY KEY AUTOINCREMENT,lab_no TEXT UNIQUE NOT NULL,name TEXT NOT NULL,age TEXT,gender TEXT,mobile TEXT,address TEXT,doctor_id INTEGER,created_at TEXT);
    CREATE TABLE IF NOT EXISTS bills(id INTEGER PRIMARY KEY AUTOINCREMENT,bill_no TEXT UNIQUE NOT NULL,patient_id INTEGER,subtotal REAL,discount REAL,total REAL,paid REAL,due REAL,payment_mode TEXT,created_at TEXT);
    CREATE TABLE IF NOT EXISTS bill_items(id INTEGER PRIMARY KEY AUTOINCREMENT,bill_id INTEGER,test_id INTEGER,test_name TEXT,price REAL);
    CREATE TABLE IF NOT EXISTS results(id INTEGER PRIMARY KEY AUTOINCREMENT,patient_id INTEGER,test_id INTEGER,parameter TEXT,result TEXT,unit TEXT,reference_range TEXT,remarks TEXT,verified INTEGER DEFAULT 0,flag TEXT DEFAULT '');
    CREATE TABLE IF NOT EXISTS reference_ranges(id INTEGER PRIMARY KEY AUTOINCREMENT,test_id INTEGER NOT NULL,parameter TEXT NOT NULL,unit TEXT,male_range TEXT,female_range TEXT,sort_order INTEGER DEFAULT 0, UNIQUE(test_id,parameter));
    """)
    # Upgrade older DBs safely.
    settings_cols={r['name'] for r in c.execute("PRAGMA table_info(settings)").fetchall()}
    if 'report_base_url' not in settings_cols: c.execute("ALTER TABLE settings ADD COLUMN report_base_url TEXT DEFAULT ''")
    cols={r['name'] for r in c.execute("PRAGMA table_info(results)").fetchall()}
    if 'flag' not in cols: c.execute("ALTER TABLE results ADD COLUMN flag TEXT DEFAULT ''")
    if not c.execute("SELECT 1 FROM settings WHERE id=1").fetchone():
        c.execute("INSERT INTO settings VALUES(1,'National Pathology Lab','Vill. Naseebpur Mirzapur, Distt. Bijnor','8171427910','','Mohd Aleem','B.COM (DMLT)','', '')")
    existing={r["name"] for r in c.execute("SELECT name FROM tests").fetchall()}
    for t in DEFAULT_TESTS:
        if t[0] not in existing: c.execute("INSERT INTO tests(name,price,category) VALUES(?,?,?)",t)
    tests={r['name']:r['id'] for r in c.execute('SELECT id,name FROM tests').fetchall()}
    for name,rows in REPORT_CATALOG.items():
        tid=tests.get(name)
        if not tid: continue
        for i,(param,unit,male,female) in enumerate(rows):
            c.execute("INSERT OR IGNORE INTO reference_ranges(test_id,parameter,unit,male_range,female_range,sort_order) VALUES(?,?,?,?,?,?)",(tid,param,unit,male,female,i))
    c.commit(); c.close()

def next_lab():
    c=db(); n=c.execute("SELECT COUNT(*) n FROM patients").fetchone()["n"]+1; c.close(); return f"LAB-{datetime.now().strftime('%Y%m%d')}-{n:04d}"
def next_bill():
    c=db(); n=c.execute("SELECT COUNT(*) n FROM bills").fetchone()["n"]+1; c.close(); return f"BIL-{datetime.now().strftime('%Y%m%d')}-{n:04d}"

def range_flag(value, ref):
    """Return '', 'HIGH' or 'LOW' for numeric values. Text/qualitative results are never auto-flagged."""
    if value is None or not str(value).strip() or not ref: return ''
    s=str(value).strip().replace(',','')
    try: v=float(re.search(r'-?\d+(?:\.\d+)?',s).group())
    except (AttributeError,ValueError): return ''
    r=str(ref).strip().replace('≤','<=').replace('≥','>=').replace('–','-').replace('—','-')
    m=re.search(r'(-?\d+(?:\.\d+)?)\s*(?:to|-|\.\.?)\s*(-?\d+(?:\.\d+)?)',r)
    if m:
        lo,hi=float(m.group(1)),float(m.group(2))
        if v<lo: return 'LOW'
        if v>hi: return 'HIGH'
        return ''
    m=re.search(r'(?:<|<=)\s*(-?\d+(?:\.\d+)?)',r)
    if m and v>=float(m.group(1)): return 'HIGH'
    m=re.search(r'(?:>|>=)\s*(-?\d+(?:\.\d+)?)',r)
    if m and v<=float(m.group(1)): return 'LOW'
    return ''

def report_rows_for(test_id, gender, saved=None):
    c=db(); rr=c.execute("SELECT * FROM reference_ranges WHERE test_id=? ORDER BY sort_order,id",(test_id,)).fetchall(); c.close()
    saved=saved or {}
    out=[]
    for r in rr:
        key=r['parameter']; s=saved.get(key,{})
        ref=r['female_range'] if str(gender).lower().startswith('f') else r['male_range']
        out.append({'parameter':key,'unit':r['unit'] or '','male_range':r['male_range'] or '','female_range':r['female_range'] or '','reference_range':ref or '','result':s.get('result',''),'flag':range_flag(s.get('result',''),ref)})
    return out

@app.route('/')
def dashboard():
    c=db(); s={'patients':c.execute("SELECT COUNT(*) n FROM patients WHERE date(created_at)=date('now','localtime')").fetchone()['n'],'collection':c.execute("SELECT COALESCE(SUM(paid),0) n FROM bills WHERE date(created_at)=date('now','localtime')").fetchone()['n'],'pending':c.execute("SELECT COUNT(*) n FROM results WHERE verified=0").fetchone()['n'],'tests':c.execute("SELECT COUNT(*) n FROM tests").fetchone()['n']}; rows=c.execute("SELECT p.*,d.name doctor FROM patients p LEFT JOIN doctors d ON d.id=p.doctor_id ORDER BY p.id DESC LIMIT 10").fetchall(); c.close(); return render_template('dashboard.html',stats=s,recent=rows)

@app.route('/patient/new',methods=['GET','POST'])
def new_patient():
    c=db(); doctors=c.execute('SELECT * FROM doctors ORDER BY name').fetchall()
    if request.method=='POST':
        c.execute('INSERT INTO patients(lab_no,name,age,gender,mobile,address,doctor_id,created_at) VALUES(?,?,?,?,?,?,?,?)',(next_lab(),request.form['name'],request.form.get('age',''),request.form.get('gender','Male'),request.form.get('mobile',''),request.form.get('address',''),request.form.get('doctor_id') or None,datetime.now().isoformat(timespec='seconds'))); pid=c.execute('SELECT last_insert_rowid()').fetchone()[0]; c.commit(); c.close(); return redirect(url_for('billing',patient_id=pid))
    c.close(); return render_template('patient_form.html',doctors=doctors,lab_no=next_lab())

@app.route('/patients')
def patients():
    q=request.args.get('q',''); c=db(); rows=c.execute("SELECT p.*,d.name doctor FROM patients p LEFT JOIN doctors d ON d.id=p.doctor_id WHERE p.name LIKE ? OR p.mobile LIKE ? OR p.lab_no LIKE ? ORDER BY p.id DESC",(f'%{q}%',f'%{q}%',f'%{q}%')).fetchall(); c.close(); return render_template('patients.html',patients=rows,q=q)

@app.route('/billing/<int:patient_id>',methods=['GET','POST'])
def billing(patient_id):
    c=db(); p=c.execute('SELECT p.*,d.name doctor FROM patients p LEFT JOIN doctors d ON d.id=p.doctor_id WHERE p.id=?',(patient_id,)).fetchone(); tests=c.execute('SELECT * FROM tests ORDER BY category,name').fetchall()
    if request.method=='POST':
        ids=request.form.getlist('test_ids')
        if not ids: flash('Select at least one test.'); c.close(); return redirect(request.url)
        sel=c.execute('SELECT * FROM tests WHERE id IN (%s)'%(','.join('?'*len(ids))),ids).fetchall(); sub=sum(x['price'] for x in sel); disc=float(request.form.get('discount') or 0); total=max(0,sub-disc); paid=float(request.form.get('paid') or 0); bid=c.execute('INSERT INTO bills(bill_no,patient_id,subtotal,discount,total,paid,due,payment_mode,created_at) VALUES(?,?,?,?,?,?,?,?,?)',(next_bill(),patient_id,sub,disc,total,paid,max(0,total-paid),request.form.get('payment_mode','Cash'),datetime.now().isoformat(timespec='seconds'))).lastrowid; c.executemany('INSERT INTO bill_items(bill_id,test_id,test_name,price) VALUES(?,?,?,?)',[(bid,x['id'],x['name'],x['price']) for x in sel]); c.commit(); c.close(); return redirect(url_for('bill_pdf',bill_id=bid))
    c.close(); return render_template('billing.html',patient=p,tests=tests)

def local_ip():
    """Best-effort LAN address for QR codes when the lab runs locally."""
    try:
        sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        sock.connect(('8.8.8.8',80))
        ip=sock.getsockname()[0]
        sock.close()
        return ip
    except Exception:
        return '127.0.0.1'

def report_public_url(patient_id, settings_row):
    base=(settings_row['report_base_url'] or '').strip().rstrip('/')
    if base:
        return f"{base}/report/{patient_id}/view"
    return f"http://{local_ip()}:5000/report/{patient_id}/view"

def make_qr(url):
    try:
        import qrcode
        img=qrcode.make(url)
        out=io.BytesIO(); img.save(out,format='PNG'); out.seek(0)
        return out
    except Exception:
        return None

@app.route('/bill/<int:bill_id>/pdf')
def bill_pdf(bill_id):
    c=db(); b=c.execute('SELECT b.*,p.* FROM bills b JOIN patients p ON p.id=b.patient_id WHERE b.id=?',(bill_id,)).fetchone(); items=c.execute('SELECT * FROM bill_items WHERE bill_id=?',(bill_id,)).fetchall(); s=c.execute('SELECT * FROM settings WHERE id=1').fetchone(); c.close()
    # 80 mm thermal-style receipt. Height grows with the number of tests.
    height=max(150*mm, (115 + 14*len(items))*mm/1.0)
    buf=io.BytesIO(); pdf=canvas.Canvas(buf,pagesize=(80*mm,height)); w,h=80*mm,height
    y=h-10*mm
    pdf.setFont('Helvetica-Bold',11); pdf.drawCentredString(w/2,y,s['lab_name'][:35]); y-=5*mm
    pdf.setFont('Helvetica',7); pdf.drawCentredString(w/2,y,(s['address'] or '')[:55]); y-=4*mm
    pdf.drawCentredString(w/2,y,'Phone: '+(s['phone'] or '')); y-=6*mm
    pdf.line(4*mm,y,w-4*mm,y); y-=5*mm
    pdf.setFont('Helvetica',7.5)
    for label,val in [('Bill No.',b['bill_no']),('Lab No.',b['lab_no']),('Patient',b['name']),('Age/Sex',f"{b['age']} / {b['gender']}"),('Date',datetime.now().strftime('%d-%m-%Y'))]:
        pdf.drawString(4*mm,y,f'{label}:'); pdf.drawRightString(w-4*mm,y,str(val)[:48]); y-=4.2*mm
    y-=2*mm; pdf.line(4*mm,y,w-4*mm,y); y-=5*mm
    pdf.setFont('Helvetica-Bold',7.5); pdf.drawString(4*mm,y,'Test'); pdf.drawRightString(w-4*mm,y,'Amount'); y-=4.5*mm
    pdf.setFont('Helvetica',7.2)
    for x in items:
        name=x['test_name'][:42]; pdf.drawString(4*mm,y,name); pdf.drawRightString(w-4*mm,y,f"Rs. {x['price']:.0f}"); y-=4.2*mm
    y-=2*mm; pdf.line(4*mm,y,w-4*mm,y); y-=5*mm
    pdf.setFont('Helvetica',7.5)
    for k,v in [('Subtotal',b['subtotal']),('Discount',b['discount']),('Total',b['total']),('Paid',b['paid']),('Due',b['due'])]:
        pdf.drawString(30*mm,y,k+':'); pdf.drawRightString(w-4*mm,y,f"Rs. {v:.2f}"); y-=4.2*mm
    y-=3*mm; pdf.drawCentredString(w/2,y,'Thank you'); y-=4*mm
    pdf.setFont('Helvetica',6.5); pdf.drawCentredString(w/2,y,'Computer generated bill')
    pdf.save(); buf.seek(0); return send_file(buf,mimetype='application/pdf',download_name=b['bill_no']+'.pdf')

@app.route('/report/<int:patient_id>',methods=['GET','POST'])
def report(patient_id):
    c=db(); p=c.execute('SELECT p.*,d.name doctor FROM patients p LEFT JOIN doctors d ON d.id=p.doctor_id WHERE p.id=?',(patient_id,)).fetchone(); ts=c.execute('SELECT DISTINCT bi.test_id,bi.test_name FROM bill_items bi JOIN bills b ON b.id=bi.bill_id WHERE b.patient_id=? ORDER BY bi.test_name',(patient_id,)).fetchall()
    if not p: c.close(); return 'Patient not found',404
    if request.method=='POST':
        c.execute('DELETE FROM results WHERE patient_id=?',(patient_id,)); remarks=request.form.get('remarks','')
        for t in ts:
            rr=c.execute('SELECT * FROM reference_ranges WHERE test_id=? ORDER BY sort_order,id',(t['test_id'],)).fetchall()
            for i,r in enumerate(rr):
                val=request.form.get(f"result_{t['test_id']}_{i}",'').strip(); ref=r['female_range'] if str(p['gender']).lower().startswith('f') else r['male_range']; flag=range_flag(val,ref)
                c.execute('INSERT INTO results(patient_id,test_id,parameter,result,unit,reference_range,remarks,verified,flag) VALUES(?,?,?,?,?,?,?,?,?)',(patient_id,t['test_id'],r['parameter'],val,r['unit'],ref,remarks,1 if val else 0,flag))
        c.commit(); c.close(); return redirect(url_for('report_pdf',patient_id=patient_id))
    saved_rows=c.execute('SELECT * FROM results WHERE patient_id=? ORDER BY test_id,id',(patient_id,)).fetchall(); saved={}
    for r in saved_rows: saved.setdefault(r['test_id'],{})[r['parameter']]={'result':r['result']}
    sections=[]
    for t in ts: sections.append({'test_id':t['test_id'],'test_name':t['test_name'],'rows':report_rows_for(t['test_id'],p['gender'],saved.get(t['test_id'],{}))})
    remarks=saved_rows[0]['remarks'] if saved_rows else ''
    c.close(); return render_template('report.html',patient=p,sections=sections,remarks=remarks)

@app.route('/report/<int:patient_id>/view')
def report_view(patient_id):
    c=db(); p=c.execute('SELECT p.*,d.name doctor FROM patients p LEFT JOIN doctors d ON d.id=p.doctor_id WHERE p.id=?',(patient_id,)).fetchone(); rows=c.execute('SELECT r.*,t.name test_name FROM results r JOIN tests t ON t.id=r.test_id WHERE r.patient_id=? ORDER BY r.test_id,r.id',(patient_id,)).fetchall(); s=c.execute('SELECT * FROM settings WHERE id=1').fetchone(); c.close()
    if not p: return 'Patient not found',404
    return render_template('report_public.html',patient=p,rows=rows,settings=s)

@app.route('/report/<int:patient_id>/pdf')
def report_pdf(patient_id):
    """Print only the actual reports: one test/report per A4 page.
    If a patient has CBC + LFT, page 1 is CBC and page 2 is LFT.
    The pre-printed stationery/header is intentionally NOT drawn by software.
    """
    c=db()
    p=c.execute('SELECT p.*,d.name doctor FROM patients p LEFT JOIN doctors d ON d.id=p.doctor_id WHERE p.id=?',(patient_id,)).fetchone()
    rows=c.execute('SELECT r.*,t.name test_name FROM results r JOIN tests t ON t.id=r.test_id WHERE r.patient_id=? ORDER BY r.test_id,r.id',(patient_id,)).fetchall()
    s=c.execute('SELECT * FROM settings WHERE id=1').fetchone()
    c.close()
    if not p: return 'Patient not found',404
    if not rows: return 'Report has no saved results yet.',400

    # Group rows by test, preserving the database order.
    groups=[]
    current=None
    for r in rows:
        if current is None or r['test_id'] != current['test_id']:
            current={'test_id':r['test_id'],'test_name':r['test_name'],'rows':[],'remarks':r['remarks'] or ''}
            groups.append(current)
        current['rows'].append(r)

    buf=io.BytesIO(); pdf=canvas.Canvas(buf,pagesize=A4); w,h=A4
    left=45; right=w-45

    for gi,g in enumerate(groups):
        # One complete test/report occupies exactly one A4 page.
        pdf.setFillColor(colors.HexColor('#12304A'))
        pdf.setFont('Helvetica-Bold',16)
        pdf.drawString(left,h-58,g['test_name'][:72])
        pdf.setFillColor(colors.black)
        pdf.setFont('Helvetica',9)
        pdf.drawString(left,h-76,f"Lab No.: {p['lab_no']}")
        pdf.drawString(205,h-76,f"Patient: {p['name']}")
        pdf.drawString(430,h-76,f"Age/Sex: {p['age']} / {p['gender']}")
        pdf.drawString(left,h-91,f"Ref. Doctor: {p['doctor'] or '—'}")
        pdf.drawRightString(right,h-91,f"Report Date: {datetime.now().strftime('%d-%m-%Y')}")

        table_top=h-118
        row_h=24 if len(g['rows']) <= 18 else max(17, int((h-300)/max(1,len(g['rows']))))
        fs=11 if row_h>=22 else 9.5
        cols=[left, 270, 350, 410, 470, right]
        pdf.setFillColor(colors.HexColor('#EAF0F5'))
        pdf.rect(left,table_top-22,right-left,22,fill=1,stroke=0)
        pdf.setFillColor(colors.black)
        pdf.setFont('Helvetica-Bold',fs)
        # Fixed column boundaries: Parameter | Result | Flag | Unit | Reference Range
        pdf.drawString(cols[0]+5,table_top-15,'Parameter')
        pdf.drawString(cols[1]+5,table_top-15,'Result')
        pdf.drawString(cols[2]+5,table_top-15,'Flag')
        pdf.drawString(cols[3]+5,table_top-15,'Unit')
        pdf.drawString(cols[4]+5,table_top-15,'Reference Range')
        y=table_top-22

        for r in g['rows']:
            y-=row_h
            pdf.setStrokeColor(colors.HexColor('#D7DEE5')); pdf.line(left,y,right,y)
            pdf.setFillColor(colors.black)
            pdf.setFont('Helvetica',fs)
            pdf.drawString(cols[0]+5,y+7,str(r['parameter'])[:34])
            result=str(r['result'] or '')[:20]
            pdf.drawString(cols[1]+5,y+7,result)
            if r['flag']:
                pdf.setFont('Helvetica-Bold',fs)
                pdf.setFillColor(colors.red if r['flag']=='HIGH' else colors.HexColor('#185ABC'))
                pdf.drawString(cols[2]+5,y+7,r['flag'])
                pdf.setFillColor(colors.black)
            pdf.setFont('Helvetica',fs)
            pdf.drawString(cols[3]+5,y+7,str(r['unit'] or '')[:12])
            pdf.drawString(cols[4]+5,y+7,str(r['reference_range'] or '')[:18])

        # Remarks, signature and QR stay on the same page.
        bottom=max(125,y-35)
        pdf.setFont('Helvetica-Bold',9.5); pdf.drawString(left,bottom,'Remarks:')
        pdf.setFont('Helvetica',9); pdf.drawString(left+52,bottom,(g['remarks'] or '')[:115])

        sig=s['signature_path']
        if sig:
            sp=os.path.join(APP_DIR,'static',sig)
            if os.path.exists(sp):
                try: pdf.drawImage(sp,right-135,bottom-5,width=85,height=38,preserveAspectRatio=True,mask='auto')
                except: pass
        pdf.setFont('Helvetica-Bold',9.5); pdf.drawString(right-135,bottom-17,(s['authorized_name'] or '')[:34])
        pdf.setFont('Helvetica',7.5); pdf.drawString(right-135,bottom-28,(s['qualification'] or 'Authorized Signatory')[:34])

        qr=make_qr(report_public_url(patient_id,s))
        if qr:
            try: pdf.drawImage(ImageReader(qr),right-58,bottom-82,width=42,height=42,mask='auto')
            except: pass
        pdf.setFont('Helvetica',6.5); pdf.drawRightString(right,bottom-90,'Scan QR to open full report')
        pdf.setFillColor(colors.HexColor('#555555')); pdf.setFont('Helvetica',7)
        pdf.drawCentredString(w/2,30,'This report is for diagnostic purpose only. Kindly correlate clinically.')
        pdf.setFillColor(colors.black)
        if gi < len(groups)-1: pdf.showPage()
    pdf.save(); buf.seek(0)
    return send_file(buf,mimetype='application/pdf',download_name=p['lab_no']+'_reports.pdf')

@app.route('/reports')
def reports():
    q=request.args.get('q','').strip(); c=db(); rows=c.execute("""SELECT p.*,d.name doctor,COALESCE((SELECT COUNT(*) FROM results r WHERE r.patient_id=p.id AND r.result<>''),0) report_count
        FROM patients p LEFT JOIN doctors d ON d.id=p.doctor_id
        WHERE p.name LIKE ? OR p.mobile LIKE ? OR p.lab_no LIKE ? ORDER BY p.id DESC""",(f'%{q}%',f'%{q}%',f'%{q}%')).fetchall(); c.close(); return render_template('reports.html',patients=rows,q=q)

@app.route('/ranges',methods=['GET','POST'])
def ranges():
    c=db()
    if request.method=='POST':
        ids=request.form.getlist('range_id')
        for rid in ids:
            c.execute('UPDATE reference_ranges SET parameter=?,unit=?,male_range=?,female_range=? WHERE id=?',(request.form.get(f'parameter_{rid}','').strip(),request.form.get(f'unit_{rid}','').strip(),request.form.get(f'male_{rid}','').strip(),request.form.get(f'female_{rid}','').strip(),rid))
        c.commit(); c.close(); flash('Male/Female reference ranges saved.'); return redirect(url_for('ranges'))
    q=request.args.get('q','').strip(); rows=c.execute("SELECT rr.*,t.name test_name,t.category FROM reference_ranges rr JOIN tests t ON t.id=rr.test_id WHERE t.name LIKE ? OR rr.parameter LIKE ? ORDER BY t.category,t.name,rr.sort_order,rr.id",(f'%{q}%',f'%{q}%')).fetchall(); c.close(); return render_template('ranges.html',ranges=rows,q=q)

@app.route('/doctors',methods=['GET','POST'])
def doctors():
    c=db()
    if request.method=='POST': c.execute('INSERT INTO doctors(name,qualification,phone) VALUES(?,?,?)',(request.form['name'],request.form.get('qualification',''),request.form.get('phone',''))); c.commit()
    rows=c.execute('SELECT * FROM doctors ORDER BY name').fetchall(); c.close(); return render_template('doctors.html',doctors=rows)

@app.route('/tests',methods=['GET','POST'])
def tests():
    c=db()
    if request.method=='POST':
        a=request.form.get('action')
        if a=='add':
            c.execute('INSERT INTO tests(name,price,category) VALUES(?,?,?)',(request.form['name'],float(request.form['price']),request.form.get('category','Custom'))); tid=c.execute('SELECT last_insert_rowid()').fetchone()[0]; c.execute("INSERT INTO reference_ranges(test_id,parameter,unit,male_range,female_range,sort_order) VALUES(?,?,?,?,?,0)",(tid,'Result','','Method dependent','Method dependent'))
        elif a=='update': c.execute('UPDATE tests SET name=?,price=?,category=? WHERE id=?',(request.form['name'],float(request.form['price']),request.form.get('category','Custom'),request.form['id']))
        elif a=='delete': c.execute('DELETE FROM tests WHERE id=?',(request.form['id'],))
        c.commit(); c.close(); return redirect(url_for('tests'))
    q=request.args.get('q',''); rows=c.execute('SELECT * FROM tests WHERE name LIKE ? OR category LIKE ? ORDER BY category,name',(f'%{q}%',f'%{q}%')).fetchall(); c.close(); return render_template('tests.html',tests=rows,q=q)

@app.route('/settings',methods=['GET','POST'])
def settings():
    c=db(); s=c.execute('SELECT * FROM settings WHERE id=1').fetchone()
    if request.method=='POST':
        sig=s['signature_path']; f=request.files.get('signature')
        if f and f.filename:
            os.makedirs(os.path.join(APP_DIR,'static','uploads'),exist_ok=True); sig='uploads/signature.png'; f.save(os.path.join(APP_DIR,'static',sig))
        c.execute('UPDATE settings SET lab_name=?,address=?,phone=?,email=?,authorized_name=?,qualification=?,signature_path=?,report_base_url=? WHERE id=1',(request.form['lab_name'],request.form['address'],request.form['phone'],request.form.get('email',''),request.form['authorized_name'],request.form.get('qualification',''),sig,request.form.get('report_base_url','').strip())); c.commit(); s=c.execute('SELECT * FROM settings WHERE id=1').fetchone()
    c.close(); return render_template('settings.html',settings=s)

init_db()
if __name__=='__main__':
    if getattr(sys, 'frozen', False):
        try:
            import webview
            def start_server():
                app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
            threading.Thread(target=start_server, daemon=True).start()
            webview.create_window('National Pathology Lab', 'http://127.0.0.1:5000', width=1400, height=900, min_size=(1000,700))
            webview.start()
        except Exception:
            threading.Timer(1.2, lambda: webbrowser.open('http://127.0.0.1:5000')).start()
            app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
    else:
        app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
