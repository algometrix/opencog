from math import fabs
from numpy import convolve
from numpy import NINF as NEGATIVE_INFINITY
from scipy.spatial.distance import cosine
from scipy.stats.distributions import uniform_gen
from spatiotemporal.temporal_events.trapezium_formulas import function_convolution_uniform
from spatiotemporal.temporal_events.util import calculate_bounds_of_probability_distribution
from spatiotemporal.temporal_interval_handling import calculateCenterMass
from spatiotemporal.time_intervals import TimeInterval
from utility.geometric import FunctionPiecewiseLinear, FunctionHorizontalLinear, integral

__author__ = 'keyvan'


TEMPORAL_RELATIONS = {
    'p': 'precedes',
    'm': 'meets',
    'o': 'overlaps',
    'F': 'finished by',
    'D': 'contains',
    's': 'starts',
    'e': 'equals',
    'S': 'started by',
    'd': 'during',
    'f': 'finishes',
    'O': 'overlapped by',
    'M': 'met by',
    'P': 'preceded by'
}


class TemporalRelation(dict):
    all_relations = 'pmoFDseSdfOMP'

    def to_list(self):
        result = []
        for name in self.all_relations:
            result.append(self[name])
        return result

    def __repr__(self):
        return 'TemporalRelation({0})'.format(''.join([name for name in self.all_relations if self[name] > 0]))

    def __str__(self):
        return repr(self)


# Benvolution ------------------------------------------


def fn_before_point(dist, time_step):
    a, b = calculate_bounds_of_probability_distribution(dist)
    p = dist.pdf(a)
    if time_step < a:
        return 1
    if a <= time_step <= b:
        value = p * (b - time_step) - p * (time_step - a)
        if value < 0:
            return 0
        return value
    return 0
    #return integral(dist.pdf, time_step, b) - integral(dist.pdf, a, time_step)


def fn_before(dist_1, dist_2):
    return fn_after(dist_2, dist_1)


def fn_after(dist_1, dist_2):
    a1, b1 = calculate_bounds_of_probability_distribution(dist_1)
    a2, b2 = calculate_bounds_of_probability_distribution(dist_2)
    return integral(lambda z: dist_2.pdf(z) * fn_before_point(dist_1, z), min(a1, a2), max(b1, b2))
    #return fn_before(dist_2, dist_1)


def fn_same(dist_1, dist_2):
    return 1 - fabs(fn_after(dist_1, dist_2) - fn_before(dist_1, dist_2))


def ben(temporal_event_1, temporal_event_2):
    beginning_a = temporal_event_1.distribution_beginning
    ending_a = temporal_event_1.distribution_ending
    beginning_b = temporal_event_2.distribution_beginning
    ending_b = temporal_event_2.distribution_ending

    beginning_a_beginning_b = 'beg_a_beg_b'
    beginning_a_ending_b = 'beg_a_end_b'
    ending_a_beginning_b = 'end_a_beg_b'
    ending_a_ending_b = 'end_a_end_b'

    asd = fn_before(beginning_a, ending_b)

    benvolutions = {
        beginning_a_beginning_b: (
            fn_before(beginning_a, beginning_b),
            fn_same(beginning_a, beginning_b),
            fn_after(beginning_a, beginning_b)
        ),
        beginning_a_ending_b: (
            fn_before(beginning_a, ending_b),
            fn_same(beginning_a, ending_b),
            fn_after(beginning_a, ending_b)
        ),
        ending_a_beginning_b: (
            fn_before(ending_a, beginning_b),
            fn_same(ending_a, beginning_b),
            fn_after(ending_a, beginning_b)
        ),
        ending_a_ending_b: (
            fn_before(ending_a, ending_b),
            fn_same(ending_a, ending_b),
            fn_after(ending_a, ending_b)
        ),
    }

    before = 0
    same = 1
    after = 2

    return {
        'p':
            benvolutions[beginning_a_beginning_b][before] * benvolutions[beginning_a_ending_b][before] *
            benvolutions[ending_a_beginning_b][before] * benvolutions[ending_a_ending_b][before],

        'm':
            benvolutions[beginning_a_beginning_b][before] * benvolutions[beginning_a_ending_b][before] *
            benvolutions[ending_a_beginning_b][same] * benvolutions[ending_a_ending_b][before],

        'o':
            benvolutions[beginning_a_beginning_b][before] * benvolutions[beginning_a_ending_b][before] *
            benvolutions[ending_a_beginning_b][after] * benvolutions[ending_a_ending_b][before],

        'F':
            benvolutions[beginning_a_beginning_b][before] * benvolutions[beginning_a_ending_b][before] *
            benvolutions[ending_a_beginning_b][after] * benvolutions[ending_a_ending_b][same],

        'D':
            benvolutions[beginning_a_beginning_b][before] * benvolutions[beginning_a_ending_b][before] *
            benvolutions[ending_a_beginning_b][after] * benvolutions[ending_a_ending_b][after],

        's':
            benvolutions[beginning_a_beginning_b][same] * benvolutions[beginning_a_ending_b][before] *
            benvolutions[ending_a_beginning_b][after] * benvolutions[ending_a_ending_b][before],

        'e':
            benvolutions[beginning_a_beginning_b][same] * benvolutions[beginning_a_ending_b][before] *
            benvolutions[ending_a_beginning_b][after] * benvolutions[ending_a_ending_b][same],

        'S':
            benvolutions[beginning_a_beginning_b][same] * benvolutions[beginning_a_ending_b][before] *
            benvolutions[ending_a_beginning_b][after] * benvolutions[ending_a_ending_b][after],

        'd':
            benvolutions[beginning_a_beginning_b][after] * benvolutions[beginning_a_ending_b][before] *
            benvolutions[ending_a_beginning_b][after] * benvolutions[ending_a_ending_b][before],

        'f':
            benvolutions[beginning_a_beginning_b][after] * benvolutions[beginning_a_ending_b][before] *
            benvolutions[ending_a_beginning_b][after] * benvolutions[ending_a_ending_b][same],

        'O':
            benvolutions[beginning_a_beginning_b][after] * benvolutions[beginning_a_ending_b][before] *
            benvolutions[ending_a_beginning_b][after] * benvolutions[ending_a_ending_b][after],

        'M':
            benvolutions[beginning_a_beginning_b][after] * benvolutions[beginning_a_ending_b][same] *
            benvolutions[ending_a_beginning_b][after] * benvolutions[ending_a_ending_b][after],

        'P':
            benvolutions[beginning_a_beginning_b][after] * benvolutions[beginning_a_ending_b][after] *
            benvolutions[ending_a_beginning_b][after] * benvolutions[ending_a_ending_b][after],
    }

# --------------------------------------------------------


class BaseTemporalFormula(object):
    def before(self, dist_1, dist_2):
        return 0.0

    def after(self, dist_1, dist_2):
        return 1.0 - self.before(dist_1, dist_2)

    def same(self, dist_1, dist_2):
        result = 1.0 - fabs(self.after(dist_1, dist_2) - self.before(dist_1, dist_2))
        if result < 0:
            return 0
        return result


class FormulaCreator(object):
    def __init__(self, temporal_formula):
        if not isinstance(temporal_formula, BaseTemporalFormula):
            raise TypeError("'temporal_formula' should be an instance of BaseTemporalFormula")

        self.before = temporal_formula.before
        self.same = temporal_formula.same
        self.after = temporal_formula.after

    def temporal_relations_between(self, temporal_event_1, temporal_event_2):
        beginning_a, ending_a = temporal_event_1.distribution_beginning, temporal_event_1.distribution_ending
        beginning_b, ending_b = temporal_event_2.distribution_beginning, temporal_event_2.distribution_ending

        result = TemporalRelation()

        result['p'] = self.before(beginning_a, beginning_b) * self.before(beginning_a, ending_b) *\
            self.before(ending_a, beginning_b) * self.before(ending_a, ending_b)

        result['m'] = self.before(beginning_a, beginning_b) * self.before(beginning_a, ending_b) *\
            self.same(ending_a, beginning_b) * self.before(ending_a, ending_b)

        result['o'] = self.before(beginning_a, beginning_b) * self.before(beginning_a, ending_b) *\
            self.after(ending_a, beginning_b) * self.before(ending_a, ending_b)

        result['F'] = self.before(beginning_a, beginning_b) * self.before(beginning_a, ending_b) *\
            self.after(ending_a, beginning_b) * self.same(ending_a, ending_b)

        result['D'] = self.before(beginning_a, beginning_b) * self.before(beginning_a, ending_b) *\
            self.after(ending_a, beginning_b) * self.after(ending_a, ending_b)

        result['s'] = self.same(beginning_a, beginning_b) * self.before(beginning_a, ending_b) *\
            self.after(ending_a, beginning_b) * self.before(ending_a, ending_b)

        result['e'] = self.same(beginning_a, beginning_b) * self.before(beginning_a, ending_b) *\
            self.after(ending_a, beginning_b) * self.same(ending_a, ending_b)

        result['S'] = self.same(beginning_a, beginning_b) * self.before(beginning_a, ending_b) *\
            self.after(ending_a, beginning_b) * self.after(ending_a, ending_b)

        result['d'] = self.after(beginning_a, beginning_b) * self.before(beginning_a, ending_b) *\
            self.after(ending_a, beginning_b) * self.before(ending_a, ending_b)

        result['f'] = self.after(beginning_a, beginning_b) * self.before(beginning_a, ending_b) *\
            self.after(ending_a, beginning_b) * self.same(ending_a, ending_b)

        result['O'] = self.after(beginning_a, beginning_b) * self.before(beginning_a, ending_b) *\
            self.after(ending_a, beginning_b) * self.after(ending_a, ending_b)

        result['M'] = self.after(beginning_a, beginning_b) * self.same(beginning_a, ending_b) *\
            self.after(ending_a, beginning_b) * self.after(ending_a, ending_b)

        result['P'] = self.after(beginning_a, beginning_b) * self.after(beginning_a, ending_b) *\
            self.after(ending_a, beginning_b) * self.after(ending_a, ending_b)

        return result


class TemporalFormulaConvolution(BaseTemporalFormula):
    def __init__(self):
        self.convolutions = {}
        self.before_integrals = {}
        self.same_integrals = {}
        self.bounds = {}

    def function_convolution_generic(self, dist_1, dist_2, bins=50):
        a1, b1, a2, b2 = 0, 0, 0, 0
        if dist_1 in self.bounds:
            a1, b1 = self.bounds[dist_1]
        else:
            a1, b1 = calculate_bounds_of_probability_distribution(dist_1)
            self.bounds[dist_1] = a1, b1
        if dist_2 in self.bounds:
            a2, b2 = self.bounds[dist_2]
        else:
            a2, b2 = calculate_bounds_of_probability_distribution(dist_2)
            self.bounds[dist_2] = a2, b2

        if (type(dist_1.dist), type(dist_2.dist)) == (uniform_gen, uniform_gen):
            return function_convolution_uniform((a1, b1), (a2, b2))

        convolution_bounds_a, convolution_bounds_b = min(a1, a2), max(b1, b2)

        delta = fabs(convolution_bounds_a - convolution_bounds_b) / bins
        convolution_interval = TimeInterval(convolution_bounds_a, convolution_bounds_b, bins)
        x = [dist_1.pdf(t) for t in convolution_interval]
        y = [dist_2.pdf(t) for t in reversed(convolution_interval)]

        c = convolve(x, y)
        dictionary_convolution = {}
        for t in xrange(len(c)):
            dictionary_convolution[delta * t] = c[t]
        bias = calculateCenterMass(dictionary_convolution)[0] + dist_2.mean() - dist_1.mean()
        dictionary_convolution_biased = {}
        for t in dictionary_convolution:
            dictionary_convolution_biased[t - bias] = dictionary_convolution[t]

        convolution_function = FunctionPiecewiseLinear(dictionary_convolution_biased, FunctionHorizontalLinear(0))
        return convolution_function.normalised()

    def duration(self, dist):
        a, b = 0, 0
        if dist in self.bounds:
            a, b = self.bounds[dist]
        else:
            a, b = calculate_bounds_of_probability_distribution(dist)
            self.bounds[dist] = a, b
        return b - a

    def before(self, dist_1, dist_2):
        if (dist_1, dist_2) in self.before_integrals:
            return self.before_integrals[(dist_1, dist_2)]

        if (dist_1, dist_2) in self.convolutions:
            convolution = self.convolutions[(dist_1, dist_2)]
        else:
            convolution = self.function_convolution_generic(dist_1, dist_2)
            self.convolutions[(dist_1, dist_2)] = convolution

        result = integral(convolution, NEGATIVE_INFINITY, 0)
        self.before_integrals[(dist_1, dist_2)] = result

        return result

    def same(self, dist_1, dist_2):
        if (dist_1, dist_2) in self.same_integrals:
            return self.same_integrals[(dist_1, dist_2)]

        if (dist_1, dist_2) in self.convolutions:
            convolution = self.convolutions[(dist_1, dist_2)]
        else:
            convolution = self.function_convolution_generic(dist_1, dist_2)
            self.convolutions[(dist_1, dist_2)] = convolution

        a1, b1 = self.bounds[dist_1]
        a2, b2 = self.bounds[dist_2]

        integral_length = fabs(max(a1, a2) - min(b1, b2))

        result = integral(convolution, -integral_length, integral_length)
        self.same_integrals[(dist_1, dist_2)] = result

        return result


class TemporalFormulaCosineConvolution(TemporalFormulaConvolution):
    def __init__(self):
        self.cosines = {}
        TemporalFormulaConvolution.__init__(self)

    def function_cosine(self, dist_1, dist_2, bins=50):
        a1, b1, a2, b2 = 0, 0, 0, 0
        if dist_1 in self.bounds:
            a1, b1 = self.bounds[dist_1]
        else:
            a1, b1 = calculate_bounds_of_probability_distribution(dist_1)
            self.bounds[dist_1] = a1, b1
        if dist_2 in self.bounds:
            a2, b2 = self.bounds[dist_2]
        else:
            a2, b2 = calculate_bounds_of_probability_distribution(dist_2)
            self.bounds[dist_2] = a2, b2

        cosine_bounds_a, cosine_bounds_b = min(a1, a2), max(b1, b2)

        delta = fabs(cosine_bounds_a - cosine_bounds_b) / bins
        convolution_interval = TimeInterval(cosine_bounds_a, cosine_bounds_b, bins)
        #convolution_interval = linspace(cosine_bounds_a, cosine_bounds_b, bins)
        x = [dist_1.pdf(t) for t in convolution_interval]
        y = [dist_2.pdf(t) for t in convolution_interval]

        return cosine(x, y)

    def same(self, dist_1, dist_2):
        return 1 - self.function_cosine(dist_1, dist_2)

    def before(self, dist_1, dist_2):
        return TemporalFormulaConvolution.before(self, dist_1, dist_2) # * (1 - self.same(dist_1, dist_2))

    def after(self, dist_1, dist_2):
        return TemporalFormulaConvolution.after(self, dist_1, dist_2) # * (1 - self.same(dist_1, dist_2))


def test(event_1, event_2, prec=0.25, size=10000):
    import matplotlib.pyplot as plt

    times_overlapped = float(0)
    times_preceded = float(0)
    times_met = float(0)
    x = []

    for i in xrange(size):
        instance_1 = event_1.instance()
        instance_2 = event_2.instance()
        d = instance_1.a - instance_2.a

        if fabs(d) <= prec:
            times_met += 1
        elif instance_1.b < instance_2.a:
            times_preceded += 1
        else:
            times_overlapped += 1
        x.append(d)

    o = times_overlapped / size
    p = times_preceded / size
    m = times_met / size
    print 'after:', o
    print 'same:', m
    print 'before:', p

    plt.hist(x, 50, normed=True)

if __name__ == '__main__':
    from scipy.stats import norm, uniform, expon
    from numpy import linspace
    import matplotlib.pyplot as plt
    from numpy import float64
    tfc = TemporalFormulaConvolution()
    fc = FormulaCreator(tfc)

    #F = uniform(loc=20, scale=2)
    #G = norm(loc=21, scale=0.2)

    #plt.plot([20, 22], [0.5, 0.5])
    #x = linspace(0, 43, 200)
    #plt.plot(x, G.pdf(x))
    #
    #print fc.same(F, G)
    #
    #plt.figure()
    #print calculate_bounds_of_probability_distribution(G)
    #
    #tfc.convolutions[(F, G)].plot()
    #plt.show()
    #
    F = uniform(loc=20, scale=5)
    for func, name in [(fc.before, 'Before'), (fc.same, 'Same'), (fc.after, 'After')]:
        print name, '-----------------------'
        for i in xrange(40):
            G_a = 30 - float64(i) * 0.4
            if i == 100:
                pass
            G = uniform(loc=G_a, scale=0.5)
            if i == 22:
                pass
            print func(F, G)

#
#if __name__ == '__main__':
#    from scipy.stats import norm, uniform, expon
#    from spatiotemporal.temporal_events import TemporalEvent, TemporalEventPiecewiseLinear
#    import matplotlib.pyplot as plt
#
#    figure_number = 1
#    for event_1, event_2 in [
#        (
#            TemporalEvent(uniform(loc=0, scale=2), uniform(loc=3, scale=2)),
#            TemporalEvent(uniform(loc=3, scale=2), uniform(loc=6, scale=2))
#        ),
#
#        (
#            TemporalEvent(uniform(loc=1, scale=4), uniform(loc=6, scale=4)),
#            TemporalEvent(uniform(loc=8, scale=5), uniform(loc=15, scale=4))
#        ),
#
#        (
#            TemporalEvent(uniform(loc=0, scale=2), uniform(loc=6, scale=4)),
#            TemporalEvent(uniform(loc=3, scale=2), uniform(loc=13, scale=4))
#        ),
#
#        (
#            TemporalEvent(uniform(loc=1, scale=4), uniform(loc=6, scale=4)),
#            TemporalEvent(uniform(loc=0, scale=11), uniform(loc=13, scale=4))
#        ),
#
#        (
#            TemporalEvent(uniform(loc=2, scale=2), uniform(loc=7, scale=2)),
#            TemporalEvent(uniform(loc=1, scale=4), uniform(loc=6, scale=4))
#        ),
#
#        #(
#        #    TemporalEvent(uniform(loc=1, scale=2), uniform(loc=4, scale=2)),
#        #    TemporalEvent(uniform(loc=6, scale=2), uniform(loc=9, scale=2))
#        #),
#        #
#        #(
#        #    TemporalEvent(uniform(loc=0, scale=3), uniform(loc=15, scale=2)),
#        #    TemporalEvent(uniform(loc=5, scale=2), uniform(loc=9, scale=3))
#        #),
#        #
#        #(
#        #    TemporalEvent(uniform(loc=5, scale=3), uniform(loc=9, scale=2)),
#        #    TemporalEvent(uniform(loc=1, scale=2), uniform(loc=15, scale=3))
#        #),
#        #
#        #(
#        #    TemporalEvent(uniform(loc=0, scale=2), uniform(loc=10, scale=2)),
#        #    TemporalEvent(uniform(loc=15, scale=2), uniform(loc=25, scale=2))
#        #),
#        #
#        #(
#        #    TemporalEvent(uniform(loc=15, scale=2), uniform(loc=25, scale=2)),
#        #    TemporalEvent(uniform(loc=0, scale=2), uniform(loc=10, scale=2))
#        #),
#
#        #(
#        #    TemporalEvent(norm(loc=1, scale=4.5), expon(loc=30, scale=2)),
#        #    TemporalEvent(norm(loc=25, scale=4.5), expon(loc=60, scale=2))
#        #),
#        #
#        #(
#        #    TemporalEvent(expon(loc=1, scale=4.5), norm(loc=30, scale=2)),
#        #    TemporalEvent(expon(loc=25, scale=4.5), norm(loc=60, scale=2))
#        #),
#        #
#        #(
#        #    TemporalEventPiecewiseLinear({1: 0, 2: 0.1, 3: 0.3, 4: 0.7, 5: 1}, {6: 1, 7: 0.9, 8: 0.6, 9: 0.1, 10: 0}),
#        #    TemporalEventPiecewiseLinear({7.5: 0, 8.5: 0.1, 9.5: 0.3, 10.5: 0.7, 11.5: 1},
#        #                                 {13: 1, 14.5: 0.9, 15.3: 0.6, 17: 0.1, 20: 0})
#        #),
#    ]:
#        tfc = TemporalFormulaConvolution()
#        fc = FormulaCreator(tfc)
#
#        temporal_relations = fc.temporal_relations_between(event_1, event_2)
#
#        print '\nFigure' + str(figure_number)
#        print '----------------------'
#        #print sum(temporal_relations.values())
#        for p in 'pmoFDseSdfOMP':
#            print p, temporal_relations[p]
#
#        figure_number += 1
#
#        #print ben(event_1, event_2)
#
#        #self = fc
#        #beginning_a = event_1.distribution_beginning
#        #ending_a = event_1.distribution_ending
#        #beginning_b = event_2.distribution_beginning
#        #ending_b = event_2.distribution_ending
#        #
#        #print self.same(beginning_a, beginning_b)
#        #print self.same(beginning_a, ending_b)
#        #print self.same(ending_a, beginning_b)
#        #print self.same(ending_a, ending_b)
#        #print self.after(beginning_a, beginning_b)
#        #print self.before(beginning_a, ending_b)
#        #print self.after(ending_a, beginning_b)
#        #print self.after(ending_a, ending_b)
#
#        #event_1.plot().ylim(ymin=-0.1, ymax=1.1)
#        #event_2.plot().figure()
#
#    #plt.show()
