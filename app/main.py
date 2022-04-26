from __future__ import print_function
import sys
import os
import uuid

import bioc
import tqdm
import tempfile
import string

from flask import Flask
from flask import render_template
from flask import request
from flask import Response



from pathlib2 import Path
from bioc import biocxml

from negbio.chexpert.stages.aggregate import NegBioAggregator
from negbio.chexpert.stages.classify import ModifiedDetector, CATEGORIES
from negbio.chexpert.stages.extract import NegBioExtractor
from negbio.chexpert.stages.load import NegBioLoader
from negbio.cli_utils import parse_args, get_absolute_path
from negbio.pipeline import text2bioc, negdetect
from negbio.pipeline.parse import NegBioParser
from negbio.pipeline.ptb2ud import NegBioPtb2DepConverter, Lemmatizer
from negbio.pipeline.ssplit import NegBioSSplitter




app = Flask(__name__)


@app.route("/hello")
def hello():
    version = "{}.{}".format(sys.version_info.major, sys.version_info.minor)
    message = "Hello World from Flask in a uWSGI Nginx Docker container with Python {} (default)".format(
        version
    )
    return message


@app.route('/')
def index():
    print('request for index page')
    return render_template('index.html')

@app.route('/Negex', methods=['GET', 'POST'])
def NegBioReport():
    report = request.form.get('report')
    print('report = '+report)
    collection = parseReport(report)
    strData = BiocCollectionToStr(collection)
    

    return Response(strData , mimetype='text/xml')


def BiocDocumentToStr(document):
    collection = bioc.BioCCollection()
    collection.add_document(document)
    return BiocCollectionToStr(collection)

def BiocCollectionToStr(collection):
    tmp = tempfile.NamedTemporaryFile()
    with open(tmp.name, 'w') as fp:
        bioc.dump(collection, fp)
    text_file = open(tmp.name, "r")
    #read whole file to a string
    data = text_file.read()

    #close file
    text_file.close()
    return data

def parseReport( reportText):
    lemmatizer = Lemmatizer()
    ptb2dep = NegBioPtb2DepConverter(lemmatizer, universal=True)
    ssplitter = NegBioSSplitter()
    parser = NegBioParser()

    print('Initialized lemma through parser')
    # chexpert
    loader = NegBioLoader()
    extractor = NegBioExtractor(Path('negbio/chexpert/phrases/mention'),
                                Path('negbio/chexpert/phrases/unmention'),
                                verbose=True)
    neg_detector = ModifiedDetector('negbio/chexpert/patterns/pre_negation_uncertainty.txt',
                                    'negbio/chexpert/patterns/negation.txt',
                                    'negbio/chexpert/patterns/post_negation_uncertainty.txt')
    aggregator = NegBioAggregator(CATEGORIES, verbose=True)

    

    id =str(uuid.uuid4())
    print('docuemntId = '+id)
    document = text2bioc.text2document(id, reportText)
    collection = bioc.BioCCollection()
    collection.add_document(document)
    return pipeline(collection, loader, ssplitter, extractor, parser, ptb2dep, neg_detector, aggregator)
   

def pipeline(collection, loader, ssplitter, extractor, parser, ptb2dep, neg_detector, aggregator, verbose=False):
    """
    Args:
        loader (NegBioLoader)
        ssplitter (NegBioSSplitter)
        parser (NegBioParser)
        extractor (NegBioExtractor)
        ptb2dep (NegBioPtb2DepConverter)
        neg_detector (ModifiedDetector)
        aggregator (NegBioAggregator)
    """
    # for document in collection.documents:
    #
    #     for passage in document.passages:
    #         passage.text = clean(passage.text)
    #     ssplitter.split_doc(document)
    for document in tqdm.tqdm(collection.documents, disable=not verbose):
        document = loader.clean_doc(document)
        document = ssplitter.split_doc(document)
        document = extractor.extract_doc(document)
        document = parser.parse_doc(document)
        document = ptb2dep.convert_doc(document)
        document = negdetect.detect(document, neg_detector)
        document = aggregator.aggregate_doc(document)
        # remove sentence
        for passage in document.passages:
            del passage.sentences[:]

    return collection



if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5000)
