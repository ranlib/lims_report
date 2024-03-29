#!/usr/bin/env python
"""
lab report ==> LIMS report
Note:
1) list of chemicals hard coded
2) list of genes considered/chemical hard coded
"""
import os
import argparse
import datetime
import logging
import pandas

# setup logging
logger = logging.getLogger(__name__)
# FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
FORMAT = "[%(filename)s] %(message)s"
logging.basicConfig(format=FORMAT)
logging.basicConfig(encoding="utf-8")

# interval of RRDR region for rpoB
RRDR = pandas.Interval(left=426, right=452, closed="both")


def get_drug_evaluation(severity: str, antimicrobial: str, gene: str, annotation: str, amino_acid_change: str, position_within_cds: int, position_within_aa: int) -> str:
    """
    get drug evaluation based on severity and other variables
    :param str severity
    :param str antimicrobial
    :param str gene
    :param str annotation
    :param str amino_acid_change
    :param str position_within_cds
    :param str position_within_aa
    :return drug_evaluation
    """
    drug_evaluation = ""

    if severity == "R":
        if gene == "rpoB":
            if amino_acid_change in ["Leu430Pro", "Asp435Tyr", "His445Asn", "His445Ser", "His445Leu", "His445Cys", "Leu452Pro", "Ile491Phe"]:
                drug_evaluation = "Predicted low-level resistance to rifampin; may test susceptible by phenotypic methods"
            else:
                drug_evaluation = "Predicted resistance to rifampin"
        else:
            drug_evaluation = f"Mutation(s) associated with resistance to {antimicrobial} detected"

    if severity == "U":
        drug_evaluation = f"The detected mutation(s) have uncertain significance; resistance to {antimicrobial} cannot be ruled out"

    if severity == "S":
        if antimicrobial != "rifampin":
            drug_evaluation = f"No mutations associated with resistance to {antimicrobial} detected"
        else:  # rifampin
            #if (annotation == "synonymous_variant") and (position_within_cds in RRDR):
            if (annotation == "synonymous_variant") and (position_within_aa in RRDR):
                drug_evaluation = "Predicted susceptibility to rifampin. The detected synonymous mutation(s) do not confer resistance"
            else:
                drug_evaluation = "Predicted susceptibility to rifampin"

    if severity == "WT":
        drug_evaluation = f"No mutations associated with resistance to {antimicrobial} detected"

    if severity == "Insufficient Coverage":
        drug_evaluation = "Pending Retest"

    return drug_evaluation


def get_gene_drug_evaluation(chem_gene: pandas.DataFrame, gene: str) -> str:
    """
    get evaluation of drug/gene combination
    """
    severities = chem_gene["mdl_LIMSfinal"].to_list()
    nt_changes = chem_gene["Nucleotide_Change"].to_list()
    aa_changes = chem_gene["Amino_acid_Change"].to_list()
    aa_changes_with_parens = [f"({x})" for x in aa_changes]
    annotations = chem_gene["Annotation"].to_list()
    positions_within_cds = chem_gene["Position_within_CDS"].to_list()
    positions_within_aa = chem_gene["AA.pos"].to_list()

    chem_gene_eval = set()
    mutation_counter = {"R": 0, "U": 0, "S": 0}
    for i, severity in enumerate(severities):
        if severity == "R":
            chem_gene_eval.add(nt_changes[i] + " " + aa_changes_with_parens[i])
            mutation_counter["R"] += 1

        if severity == "U":
            chem_gene_eval.add(nt_changes[i] + " " + aa_changes_with_parens[i])
            mutation_counter["U"] += 1

        if severity == "S":
            #if (gene == "rpoB") and (annotations[i] == "synonymous_variant") and (positions_within_cds[i] in RRDR):
            if (gene == "rpoB") and (annotations[i] == "synonymous_variant") and (positions_within_aa[i] in RRDR):
                chem_gene_eval.add(nt_changes[i] + " " + aa_changes_with_parens[i] + "[synonymous]")
            mutation_counter["S"] += 1

        if severity == "WT":
            chem_gene_eval.add("No mutations detected")

        if severity == "Insufficient Coverage":
            chem_gene_eval.add("No sequence")

    if (mutation_counter["R"] == 0) and (mutation_counter["U"] == 0) and (mutation_counter["S"] > 0):
        chem_gene_eval = set(["No high confidence mutations detected"])

    discard_elements = set(["No mutations detected", "No sequence"])
    if (mutation_counter["R"] + mutation_counter["U"] + mutation_counter["S"]) > 0:
        chem_gene_eval = chem_gene_eval - discard_elements
            
    return "; ".join(chem_gene_eval)


def lims_report(lab_report: str, lineage_name: str, operator: str) -> pandas.DataFrame():
    """
    create LIMS report
    """
    # header of LIMS report
    header = [
        "MDL sample accession numbers",
        "M_DST_A01_ID",
        "M_DST_B01_INH",
        "M_DST_B02_katG",
        "M_DST_B03_fabG1",
        "M_DST_B04_inhA",
        "M_DST_C01_ETO",
        "M_DST_C02_ethA",
        "M_DST_C03_fabG1",
        "M_DST_C04_inhA",
        "M_DST_D01_RIF",
        "M_DST_D02_rpoB",
        "M_DST_E01_PZA",
        "M_DST_E02_pncA",
        "M_DST_F01_EMB",
        "M_DST_F02_embA",
        "M_DST_F03_embB",
        "M_DST_G01_AMK",
        "M_DST_G02_rrs",
        "M_DST_G03_eis",
        "M_DST_H01_KAN",
        "M_DST_H02_rrs",
        "M_DST_H03_eis",
        "M_DST_I01_CAP",
        "M_DST_I02_rrs",
        "M_DST_I03_tlyA",
        "M_DST_J01_MFX",
        "M_DST_J02_gyrA",
        "M_DST_J03_gyrB",
        "M_DST_K01_LFX",
        "M_DST_K02_gyrA",
        "M_DST_K03_gyrB",
        "M_DST_L01_BDQ",
        "M_DST_L02_Rv0678",
        "M_DST_L03_atpE",
        "M_DST_L04_pepQ",
        "M_DST_L05_mmpL5",
        "M_DST_L06_mmpS5",
        "M_DST_M01_CFZ",
        "M_DST_M02_Rv0678",
        "M_DST_M03_pepQ",
        "M_DST_M04_mmpL5",
        "M_DST_M05_mmpS5",
        "M_DST_N01_LZD",
        "M_DST_N02_rrl",
        "M_DST_N03_rplC",
        "Analysis date",
        "Operator",
    ]

    # map input column for drug to output LIMS report column
    drug_to_column = {
        "isoniazid": "M_DST_B01_INH",
        "ethionamide": "M_DST_C01_ETO",
        "rifampin": "M_DST_D01_RIF",
        "pyrazinamide": "M_DST_E01_PZA",
        "ethambutol": "M_DST_F01_EMB",
        "amikacin": "M_DST_G01_AMK",
        "kanamycin": "M_DST_H01_KAN",
        "capreomycin": "M_DST_I01_CAP",
        "moxifloxacin": "M_DST_J01_MFX",
        "levofloxacin": "M_DST_K01_LFX",
        "bedaquiline": "M_DST_L01_BDQ",
        "clofazimine": "M_DST_M01_CFZ",
        "linezolid": "M_DST_N01_LZD",
    }

    # map input columns for drug/gene combination to output LIMS report columns
    gene_drug_to_column = {
        ("katG", "isoniazid"): "M_DST_B02_katG",
        ("fabG1", "isoniazid"): "M_DST_B03_fabG1",
        ("inhA", "isoniazid"): "M_DST_B04_inhA",
        ("ethA", "ethionamide"): "M_DST_C02_ethA",
        ("fabG1", "ethionamide"): "M_DST_C03_fabG1",
        ("inhA", "ethionamide"): "M_DST_C04_inhA",
        ("rpoB", "rifampin"): "M_DST_D02_rpoB",
        ("pncA", "pyrazinamide"): "M_DST_E02_pncA",
        ("embA", "ethambutol"): "M_DST_F02_embA",
        ("embB", "ethambutol"): "M_DST_F03_embB",
        ("rrs", "amikacin"): "M_DST_G02_rrs",
        ("eis", "amikacin"): "M_DST_G03_eis",
        ("rrs", "kanamycin"): "M_DST_H02_rrs",
        ("eis", "kanamycin"): "M_DST_H03_eis",
        ("rrs", "capreomycin"): "M_DST_I02_rrs",
        ("tlyA", "capreomycin"): "M_DST_I03_tlyA",
        ("gyrA", "moxifloxacin"): "M_DST_J02_gyrA",
        ("gyrB", "moxifloxacin"): "M_DST_J03_gyrB",
        ("gyrA", "levofloxacin"): "M_DST_K02_gyrA",
        ("gyrB", "levofloxacin"): "M_DST_K03_gyrB",
        ("Rv0678", "bedaquiline"): "M_DST_L02_Rv0678",
        ("atpE", "bedaquiline"): "M_DST_L03_atpE",
        ("pepQ", "bedaquiline"): "M_DST_L04_pepQ",
        ("mmpL5", "bedaquiline"): "M_DST_L05_mmpL5",
        ("mmpS5", "bedaquiline"): "M_DST_L06_mmpS5",
        ("Rv0678", "clofazimine"): "M_DST_M02_Rv0678",
        ("pepQ", "clofazimine"): "M_DST_M03_pepQ",
        ("mmpL5", "clofazimine"): "M_DST_M04_mmpL5",
        ("mmpS5", "clofazimine"): "M_DST_M05_mmpS5",
        ("rrl", "linezolid"): "M_DST_N02_rrl",
        ("rplC", "linezolid"): "M_DST_N03_rplC",
    }

    # output = LIMS report
    lims = pandas.DataFrame(columns=header)

    if os.path.getsize(lab_report.name) > 0:
        # input = lab report
        lab_cols = [
            "Sample ID",
            "Position within CDS",
            "AA.pos",
            "Nucleotide Change",
            "Amino acid Change",
            "Annotation",
            "Gene Name",
            "antimicrobial",
            "mdl_LIMSfinal",
        ]
        lab = pandas.read_csv(lab_report, usecols=lab_cols)
        lab.columns = lab.columns.str.replace(" ", "_")
    else:
        logger.error(f"empty input lab report, output empty lims report")
        return lims
        
    # consider only genes of interest for LIMS report, see gene_drug_to_column dictionary hard coded above
    # get list of genes that are "reportable"
    # i.e. weed out genes that are not reportable
    genes_reportable = {key[0] for key in list(gene_drug_to_column.keys())}
    lab = lab[lab["Gene_Name"].isin(genes_reportable)]
    lab = lab.reset_index(drop=True)
        
    # mdl = category, determine sort order according to severity
    # sort by severity, keep only most severe
    lab["mdl_LIMSfinal"] = pandas.Categorical(lab["mdl_LIMSfinal"], ["R", "Insufficient Coverage", "U", "S", "WT"])
    lab_sorted = lab.sort_values(["antimicrobial", "mdl_LIMSfinal"], ascending=True)

    lims.loc[0, "MDL sample accession numbers"] = lab["Sample_ID"][0]
    lims.loc[0, "M_DST_A01_ID"] = lineage_name
    lims.loc[0, "Analysis date"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    lims.loc[0, "Operator"] = operator

    # loop over drugs and fill LIMS report
    # use only drugs in drug_to_column list, i.e. some drugs in input bed file are not considered
    for drug in drug_to_column:
        filter_chem = "antimicrobial==@drug"
        chem = lab_sorted.query(filter_chem)
        chem = chem.reset_index()
        if len(chem.index) == 0:
            logger.warning(f"no data for drug {drug}")
        else:
            logger.debug("Chemical information")
            logger.debug(chem)
            # fill drug header based on mutation with highest severity
            gene = chem.iloc[0]["Gene_Name"]
            severity = chem.iloc[0]["mdl_LIMSfinal"]
            annotation = chem.iloc[0]["Annotation"]
            amino_acid_change = chem.iloc[0]["Amino_acid_Change"]
            position_within_cds = chem.iloc[0]["Position_within_CDS"]
            position_within_aa = chem.iloc[0]["AA.pos"]
            lims.loc[0, drug_to_column[drug]] = get_drug_evaluation(severity, drug, gene, annotation, amino_acid_change, position_within_cds, position_within_aa)

            genes_for_this_chemical = [key[0] for key in list(gene_drug_to_column.keys()) if key[1] == drug]
            for gene in genes_for_this_chemical:
                # get information for gene/drug information and fill column
                filter_gene = "antimicrobial==@drug & Gene_Name==@gene"
                chem_gene = lab_sorted.query(filter_gene)
                logger.debug("Chemical/gene information")
                logger.debug(chem_gene)
                lims.loc[0, gene_drug_to_column[(gene, drug)]] = get_gene_drug_evaluation(chem_gene, gene)

    return lims


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="lims report", prog="lims_report", formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=80))
    parser.add_argument("--lab", "-l", type=argparse.FileType("r"), dest="lab", help="input lab csv report", required=True)
    parser.add_argument("--operator", "-o", type=str, dest="operator", help="input operator name", required=True)
    parser.add_argument("--lineages", "-s", type=argparse.FileType("r"), dest="lineages", help="input lineage tsv file", nargs="?")
    parser.add_argument("--lims", "-r", type=argparse.FileType("w"), dest="lims", help="output lims csv report", required=True)
    parser.add_argument("--log_level", "-d", type=str, dest="log_level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], default="INFO", help="logging level")
    args = parser.parse_args()

    # logging
    # logging.basicConfig(filename='lims_report.log')
    logger.setLevel(args.log_level)

    # get lineage from lineages file
    if args.lineages is not None:
        lineages = pandas.read_csv(args.lineages, sep="\t")
        lineage = lineages.loc[0, "Lineage Name"]
    else:
        lineage = "Lineage information not available"

    # create LIMS report
    df = lims_report(args.lab, lineage, args.operator)
    df.to_csv(args.lims, index=False)
