import re
import csv
import nltk
import time
import string
import random
import sklearn
import operator
import numpy as np
from sklearn import *
from itertools import groupby
import matplotlib.pyplot as plt
from nltk.stem.snowball import SnowballStemmer
from sklearn.base import TransformerMixin
from sklearn.preprocessing import FunctionTransformer

stop_words = set()

# TODO: Check to see if nltk has an easy way to check to see if a test is in english. (PyEnchant is an alternative)
# TODO: Look more into vectorizations and how they play a role in creating features.
# TODO: Create an excel spreadsheet for Obama: Positive/Negative, Romney: Positive/Negative, and a Neutral file.
# TODO: Reasoning for a neutral file: Since the data is neutral, we can use it in both training sets. Currently
# TODO: we are only looking at the Obama file and classifying pos,neg,neu, but we can extend our train set.
# TODO: Create functions to tune/optimize the parameters for different classifers/algorithms
# TODO: Include other algorithms besides (NNeighbor, etc).
# TODO: Once we reach here, then it's time to look at Deep-Learning if applicable.
class DenseTransformer(TransformerMixin):

    def transform(self, X, y=None, **fit_params):
        return X.todense()

    def fit_transform(self, X, y=None, **fit_params):
        self.fit(X, y, **fit_params)
        return self.transform(X)

    def fit(self, X, y=None, **fit_params):
        return self

class StemmedCountVectorizer(feature_extraction.text.CountVectorizer):
    """
    Taken from a tutorial. TODO: Provide info on what this does.
    Essentially does the same thing as StemmerPorter
    """
    def build_analyzer(self):
        stemmer = SnowballStemmer("english")
        analyzer = feature_extraction.text.CountVectorizer(analyzer='word',
                                                           tokenizer=None,
                                                           max_features=2000,
                                                           preprocessor=None,
                                                           stop_words=None).build_analyzer()
        #analyzer = super(StemmedCountVectorizer, self).build_analyzer()
        return lambda doc: ([stemmer.stem(w) for w in analyzer(doc)])


def optimize_stop_words():
    """
    Since nltk.corpus.stopwords creates a list to hold their stopwords, I created a set for quicker lookup.

    :return: returns the new set of stop words.
    """
    global stop_words
    list_stop_words = nltk.corpus.stopwords.words('english')
    for word in list_stop_words:
        stop_words.add(word)
    stop_words.add('rt')
    stop_words.add('retweet')
    stop_words.add('e')


def remove_stop_words(tweet):
    """
    Iterates through the tweet and removes any stop_words.

    :param tweet: Holds the tweet in a list form
    :return: returns the new "clean_tweet"
    """
    global stop_words
    clean_tweet = []
    for word in tweet:
        if word not in stop_words:
            clean_tweet.append(word)
    return clean_tweet


def porter_stemmer(tweet):
    """
    The following function is a built in algorithm in the nltk library.
    Essentially the PorterStemmer attempts to remove suffixes and prefixes of words
    to get to the "root" word.
    Functionality: Traverse through each word and stem the word.

    :param tweet: Holds the tweet in the form of a list.
    :return: Returns the tweet after stemming
    """
    ps = nltk.stem.PorterStemmer()
    stemmed_tweet = [ps.stem(word) for word in tweet]
    stemmed_tweet = ' '.join(stemmed_tweet)
    return str(stemmed_tweet)


def regex_tweet(regex, tweet):
    """
    The following function utilizes regular expressions to handle the raw tweets
    Uses the regex.compile from func read_tweets and replaces any findings with a space.
    Removes unnecessary trailing white spaces and ignores anything that can't be parsed in utf-8.

    :param regex: Holds the initial regex.compile from read_tweets
    :param tweet: Holds the current tweet being evaluated
    :return: Returns the tweet in list form
    """
    tweet = regex.sub(' ', tweet)
    tweet = re.sub(' +', ' ', tweet).strip()
    tweet = re.sub('[%s]' % re.escape(string.punctuation), '', tweet)
    tweet = ''.join(''.join(s)[:2] for _, s in groupby(tweet))
    tweet = tweet.encode('ascii', errors='ignore').decode('utf-8').lower()
    tweet = tweet.split()
    return tweet


def pre_processing(regex, curr_tweet):
    """
    Functionality: This function uses multiple regular expressions to remove the noise of the raw tweet.
    regex removes: links, tags to people (i.e. @Obama), any non-alphabetical character. It calls a function to remove
    all stop words and to apply the porter_stemmer algorithm (to get roots of words)

    :param regex: Holds the initial regex
    :param curr_tweet: Holds the current tweet
    :return: Returns the current tweet (in string form)
    """
    curr_tweet = regex_tweet(regex, curr_tweet)
    curr_tweet = remove_stop_words(curr_tweet)
    curr_tweet = porter_stemmer(curr_tweet)
    return curr_tweet


def valid_classification(classification):
    """
    Checks to see if valid classification according to specifications.

    :param classification: Holds the current row's classification (-1, 0, 1, 2, or 'irrelevant' in our csv files)
    :return: returns boolean if we have a valid (for our project) class
    """
    if classification == '-1' or classification == '0' or classification == '1':
        return True
    return False


def read_tweets(file_name):
    """
    The following function reads the raw tweets from the file passed in, cleans the raw tweets, then adds to a list.
    It also randomizes the data with a specific seed to 'shuffle' the data in case it is sorted in a specific way.

    :param file_name: Current file name of tweets in csv format
    :return: Returns a list that holds the cleaned tweets and classifications for each tweet for the specific file
    """

    tweet_list = []
    class_list = []

    with open(file_name, 'r', encoding='utf8') as csv_file:

        random.seed(2012)
        li = csv_file.readlines()
        header = li.pop(0)
        random.shuffle(li)
        li.insert(0, header)
        reader = csv.DictReader(li)
        #reader = csv.DictReader(csv_file)

        regex = re.compile(r'<.*?>|https?[^ ]+|([@])[^ ]+|[^a-zA-Z#\' ]+|\d+/?')

        for row in reader:
            classification = row['classification']
            if valid_classification(classification):
                clean_tweet = pre_processing(regex, row['Annotated tweet'])
                tweet_list.append(clean_tweet)
                class_list.append(row['classification'])
                #print(clean_tweet)

    return [tweet_list, class_list]


def tfidf_transform_tweets(counts):
    """
    Revisit doc
    :param counts:
    :return:
    """
    tfid_transformer = feature_extraction.text.TfidfTransformer()
    x_train_counts = tfid_transformer.fit_transform(counts)
    return x_train_counts


def count_vectorize_tweets(corpus):
    """
    revisit doc
    :param corpus:
    :return:
    """
    count_vect = feature_extraction.text.CountVectorizer()
    x_train_counts = count_vect.fit_transform(corpus)
    # print('shape:',x_train_counts.data)
    # for row in x_train_counts.data:
    #     print('row: ', row)
    #     print(str(type(row)))
    x_train_counts = tfidf_transform_tweets(x_train_counts)
    return x_train_counts


def vectorize_tweets(corpus):
    """
    Takes every tweet and essentially converts it to TF_IDF features.
    Since we are using a large dataset of tweets, there will be many words
    :param corpus:
    :return:
    """
    vectorizer = feature_extraction.text.TfidfVectorizer(max_features=3200, binary=True)
    vectors = vectorizer.fit_transform(corpus)

    # Prints the (key,vals) of the features generated from TfidfVectorizer()
    # idf = vectorizer._tfidf.idf_
    # features = dict(zip(vectorizer.get_feature_names(), idf))
    # for word in features:
    #     print('key: ', word, ' value: ', features[word])
    # print('features: ', len(features))

    return vectors


def get_average_result(actual, prediction):
    """
    Gets the average of the precision, recall, f1_score, and accuracy score of negative, neutral, and positive classes
    :param actual: List of actual test classifications
    :param prediction: Predictions of each tweet
    :return: info on predictions
    """

    labels = ['-1', '0', '1']
    avg = 'macro'

    precision = sklearn.metrics.precision_score(actual, prediction, labels=labels, average=avg)
    recall = sklearn.metrics.recall_score(actual, prediction, labels=labels, average=avg)
    f_score = sklearn.metrics.f1_score(actual, prediction, labels=labels, average=avg)
    acc = sklearn.metrics.accuracy_score(actual, prediction)

    print('Avg Precision: ', precision)
    print('Avg Recall: ', recall)
    print('Avg F1-Score: ', f_score)
    print('Avg Accuracy: ', acc)

    return [precision, recall, f_score, acc]


def get_individual_results(actual, prediction):
    """
    Similar to above function, but focuses on break down per class and category
    :param actual: List of actual test classifications
    :param prediction: Predictions of each tweet
    :return: Array that holds info per class (recall, precision, fscore, support)
    """
    labels = ['-1', '0', '1']
    avg = None
    info_for_classes = sklearn.metrics.precision_recall_fscore_support(actual, prediction, labels=labels, average=avg)

    # Prints Row: precision, recall, f_score, support | Columns: Negative, Neutral, Positive
    for c in info_for_classes:
        print(c)

    return info_for_classes


def print_models_fscores(f_scores):
    """
    The following function evaluates all the average f-scores computed from compute_classifiers(..)
    and sorts it in descending order.

    :param f_scores: Holds a map (classifier/model -> avg f score)
    :return: None
    """
    # Finding the word with the maximum length, then using that to determine padding with ljust
    col_width = max(len(classifier) for classifier in f_scores) + 2

    print('Printing Classifiers and their F_Scores in sorted order: ')
    sorted_fscores = sorted(f_scores.items(), key=operator.itemgetter(1), reverse=True)

    for fscore in sorted_fscores:
        row = 'Classifier: '
        row += ''.join(fscore[0].ljust(col_width))
        row += '\t|\tf_score: %s' % (fscore[1])
        print(row)
    print('\n')


def compute_classifiers(train_data, test_data):
    """
    The following function uses multiple classifiers and prints their results.

    :param train_data: train_data[0] holds all the tweets, train_data[1] holds all classifications
    :param test_data: test_data[0] holds all the test tweets, test_data[1] holds all classifications of test set
    :return: No return value
    """

    f_scores = {}
    avg_scores = {}
    individual_scores = {}

    classifiers = {
        'SVC': svm.SVC(kernel="rbf", gamma=1, C=1, degree=2, class_weight='balanced', random_state=47),
        # 'SGDC': SGDClassifier(loss='hinge', penalty='l2', alpha=0.001, random_state=4193),
        # 'Perceptron': Perceptron(alpha=0.001, penalty=None, class_weight='balanced', random_state=42),
        # 'LR': LogisticRegression(penalty='l2', class_weight='balanced', random_state=41),
        # 'L.SVC': LinearSVC(C=.5, class_weight='balanced'),
        # 'SVC1': SVC(C=1.0, cache_size=200, class_weight=None, coef0=0.0,
        # decision_function_shape='ovr', degree=3, gamma=3, kernel='rbf',
        # max_iter=-1, probability=False, random_state=None, shrinking=True,
        # tol=0.001, verbose=False),
        # 'SVC2': SVC(kernel="linear", gamma=3, C=1, class_weight='balanced'),
        # 'NC': NearestCentroid(),
        # 'KNN': KNeighborsClassifier(n_neighbors=150, algorithm='auto', p=2),
        #'DTree': tree.DecisionTreeClassifier(),
        # 'RF': RandomForestClassifier(),
        # 'MLP': MLPClassifier(alpha=1),
        # 'Ada': AdaBoostClassifier()
        #'NB': naive_bayes.GaussianNB()
    }

    # TODO: Look up StemmedCountVectorizer. How does this stemmer give different results to porterstemmer????!!!
    vect = StemmedCountVectorizer()
    print('\nPrinting Results of Multiple Classifiers\n')
    for classifier in classifiers.keys():
        start = time.time()

        if classifier == 'NB':
            text_stemmed = sklearn.pipeline.Pipeline([('vect', vect),
                                                      ('dense_transformer', DenseTransformer()),
                                                      ('clf', classifiers[classifier])])
        else:
            text_stemmed = sklearn.pipeline.Pipeline([('vect', vect),
                                                      ('tfidf', feature_extraction.text.TfidfTransformer()),
                                                      ('clf', classifiers[classifier])])

        print('Fitting data for:', classifier)
        text_stemmed = text_stemmed.fit(train_data[0], train_data[1])

        print('Done.')
        print('Making predictions with a 10 fold cv.')
        # prediction = text_stemmed.predict(test_data[0])
        predictions = sklearn.model_selection.cross_val_predict(text_stemmed, train_data[0],
                                                                train_data[1], n_jobs=-1, cv=10)
        print('Done.')

        print('Classifier Results: ', classifier)
        # get_individual_results(test_data[1], prediction)
        # results = get_average_result(test_data[1], prediction)
        indiv_results = get_individual_results(train_data[1], predictions)
        avg_results = get_average_result(train_data[1], predictions)

        f_scores[classifier] = avg_results[2]
        avg_scores[classifier] = avg_results
        individual_scores[classifier] = indiv_results

        end = time.time()
        print('Total Time Elapsed: ', (end - start) * 1000, '\n\n')

    print_models_fscores(f_scores)

    return [avg_scores, individual_scores]


def create_avg_graphs(obama_results, romney_results):
    """
    The following function creates the "average" graphs for each model. Average being all the classifications
    combined and shows the precision, recall, and f-scores.

    :param obama_results: Holds the individual results of positive, negative, and neutral for each model
    :param romney_results: Same as obama
    :return: No return, just plots and shows graph representations
    """

    title = ['Precision Scores', 'Recall Scores', 'F-Scores', 'Accuracy Scores']

    for i in range(4):
        objects = []
        o_scores = []
        r_scores = []

        for key in obama_results:
            objects.append(key)
            o_scores.append(obama_results[key][i])
            r_scores.append(romney_results[key][i])

        fig, ax = plt.subplots()
        index = np.arange(len(objects))
        bar_width = 0.35
        opacity = 0.5

        bar1 = plt.bar(index, o_scores, bar_width,
                       alpha=opacity,
                       color='#6C7BFF',
                       label='Obama')
        bar2 = plt.bar(index + bar_width, r_scores, bar_width,
                       alpha=opacity,
                       color='#FF6C6C',
                       label='Romney')

        plt.ylabel('Percentages')
        plt.xlabel('Models')
        plt.title(title[i])
        plt.xticks((index + (bar_width/2)), objects)
        plt.legend()
        plt.tight_layout()
        plt.show()


def create_classification_graphs(obama_results, romney_results):
    """
    The following function creates the graphs associated with each model/classifier and their classifications.

    :param obama_results: Holds the individual results of positive, negative, and neutral for each model
    :param romney_results: Same as obama
    :return: No return, just plots and shows graph representations

    TODO: Create more of a row/col table with numbers as opposed to bar graphs??
    """
    # Prints Row: precision, recall, f_score, support | Columns: Negative, Neutral, Positive
    titles = ['Precision', 'Recall', 'F-Score', 'Support']
    labels = ['Negative', 'Neutral', 'Positive']
    plt.figure(1)

    # Zip up files to do a comparison on the same graph/image
    # This for loop goes through each model
    for (omodel, rmodel) in zip(obama_results, romney_results):

        # Iterator used to grab corresponding title
        i = 0

        # This for loop goes through each array (precision, recall, f_score, support arrays)
        for (oarr, rarr) in zip(obama_results[omodel], romney_results[rmodel]):

            fig, ax = plt.subplots()
            index = np.arange(3)
            bar_width = 0.35
            opacity = 0.5
            oy = []
            ry = []

            # This for loop goes through each element in array (value of: negative, neutral, positive)
            for (onum,rnum) in zip(oarr, rarr):

                oy.append(onum)
                ry.append(rnum)

            bar1 = plt.bar(index, oy, bar_width,
                           alpha=opacity,
                           color='#6C7BFF',
                           label='SVC-Obama')

            bar2 = plt.bar(index + bar_width, ry, bar_width,
                           alpha=opacity,
                           color='#FF6C6C',
                           label='SVC-Romney')

            if titles[i] == 'Support':
                plt.ylabel('Counts')
            else:
                plt.ylabel('Percentages')
            plt.xlabel('Classifications')
            plt.title(titles[i])
            plt.xticks(np.arange(4) + (bar_width/2), labels)
            plt.legend()

            for rect in bar1:
                height = rect.get_height()
                if titles[i] != 'Support':
                    s = '%.2f' % (float(height)*100.0) + "%"
                else:
                    s = '%d' % int(height)
                ax.text(rect.get_x() + rect.get_width() / 2., 0.99 * height,
                        s, ha='center', va='bottom')
            for rect in bar2:
                height = rect.get_height()
                if titles[i] != 'Support':
                    s = '%.2f' % (float(height)*100.0) + "%"
                else:
                    s = '%d' % int(height)
                ax.text(rect.get_x() + rect.get_width() / 2., 0.99 * height,
                        s, ha='center', va='bottom')

            plt.tight_layout()
            i += 1

    plt.show()


def main():

    start = time.time()
    optimize_stop_words()

    # Clean up raw tweets
    # obama_tweets[0][x] <- holds all the tweets
    # obama_tweets[1][x] <- holds all the classifications
    print('Reading and cleaning tweets.')
    obama_tweets = read_tweets('obama.csv')
    romney_tweets = read_tweets('romney.csv')
    print('Done.')

    new_otweets = [[], []]
    new_rtweets = [[], []]

    for i in range(len(obama_tweets[0])):

        new_otweets[0].append(obama_tweets[0][i])
        new_otweets[1].append(obama_tweets[1][i])

        if obama_tweets[1][i] == '-1':
            new_rtweets[0].append(obama_tweets[0][i])
            new_rtweets[1].append('1')
        # if obama_tweets[1][i] == '1':
        #     new_rtweets[0].append(obama_tweets[0][i])
        #     new_rtweets[1].append('-1')
        # if obama_tweets[1][i] == '0':
        #     new_rtweets[0].append(obama_tweets[0][i])
        #     new_rtweets[1].append('0')

    for i in range(len(romney_tweets[0])):

        new_rtweets[0].append(romney_tweets[0][i])
        new_rtweets[1].append(romney_tweets[1][i])

        if romney_tweets[1][i] == '-1':
            new_otweets[0].append(romney_tweets[0][i])
            new_otweets[1].append('1')
        # if romney_tweets[1][i] == '1':
        #     new_otweets[0].append(romney_tweets[0][i])
        #     new_otweets[1].append('-1')
        # if romney_tweets[1][i] == '0':
        #     new_otweets[0].append(romney_tweets[0][i])
        #     new_otweets[1].append('0')



    # Not currently used
    obama_test_tweets = read_tweets('obama_test.csv')
    romney_test_tweets = read_tweets('romney_test.csv')

    # Get results from computation to use for graphs
    obama_results = compute_classifiers(new_otweets, obama_test_tweets)
    romney_results = compute_classifiers(new_rtweets, romney_test_tweets)

    # Create Graphs
    create_avg_graphs(obama_results[0], romney_results[0])
    create_classification_graphs(obama_results[1], romney_results[1])

    end = time.time()
    print('Total Executed Time: ', end - start)


if __name__ == '__main__':
    main()
