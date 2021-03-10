import ROOT
import os
import json

def find_xsec(path, xsecs):
    for key, val in xsecs.items():
        if key in path:
            return val


lumi = {"2016": 35.92, "2017": 41.53, "2018": 59.68}

# This class prepares a given sample by scaling to int. luminosity
class Sample:
    def __init__(self, name, ntuple_path, paths, isMC=True, year="2016", cut=None, limits=False, oneFile=False):
        with open(os.path.join("/vols/cms/LLP/yields_201117", year, "eventyields.json")) as json_file:
            yields = json.load(json_file)
        with open(os.path.join("/vols/cms/LLP/yields_201117", year, "eventyieldsHNL.json")) as json_file:
            yieldsHNL = json.load(json_file)        
        self.name = name
        self.file_list = ROOT.std.vector('string')()
        self.sum_weight = 0
        self.isMC = isMC
        if oneFile:
            counter = 0
        for path in paths:
            for f in os.listdir(os.path.join(ntuple_path, path)):
                self.file_list.push_back(os.path.join(ntuple_path, path, f))
                if oneFile:
                    counter +=1
                    if counter > 5:
                        break
            if self.isMC:
                if "HNL" not in name:
                    self.sum_weight += yields[path]["weighted"]
                else:
                    self.sum_weightHNL = {}
                    self.sum_weight += 1.
                    for coupling in range(2, 68):
                        self.sum_weightHNL[coupling] = yieldsHNL[path]["LHEWeights_coupling_{}".format(coupling)]
        self.rdf = ROOT.RDataFrame("Friends", self.file_list)
        count = self.rdf.Count().GetValue()
        #if count > 0:
        if cut is not None:
            self.rdf = self.rdf.Filter(cut)
        selected = self.rdf.Count().GetValue()

        print("RDF {} has entries {}/{}".format(name, selected, count))

        if self.isMC:
            if "HNL" in name:
                if not limits:
                    with open("/vols/cms/LLP/gridpackLookupTable.json") as lookup_table_file:
                        lookup_table = json.load(lookup_table_file)
                    lu_infos = lookup_table[name]['weights'][str(int(coupling))]
                    xsec = lu_infos['xsec']['nominal']
                else:
                    xsec = 1.
            else:
                with open("/vols/cms/LLP/xsec.json") as xsec_file:
                    xsecs = json.load(xsec_file)
                xsec = find_xsec(path, xsecs)
            self.rdf = self.rdf.Define("weightNominal", "IsoMuTrigger_weight_trigger_nominal*tightMuons_weight_iso_nominal*tightMuons_weight_id_nominal*tightElectrons_weight_id_nominal*puweight_nominal*genweight*tightElectrons_weight_reco_nominal*looseElectrons_weight_reco_nominal*%s*1000.0*%s/%s" %(lumi[year], xsec, self.sum_weight))

            if "HNL" in name:
                for coupling in range(2, 68):
                    self.rdf = self.rdf.Define("weightNominalHNL_{}".format(coupling), "weightNominal*LHEWeights_coupling_{}/{}".format(coupling, self.sum_weightHNL[coupling]))
        else:
            self.rdf = self.rdf.Define("weightNominal", "1")
