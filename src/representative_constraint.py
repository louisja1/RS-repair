from color_distribution import ColorDistribution
from fractions import Fraction


class RepresentativeConstraint:
    def __init__(self, vals, fractions):
        self.constraint = {}
        assert len(vals) == len(fractions)
        sum_fraction = Fraction(0, 1)
        for i in range(len(vals)):
            self.constraint[vals[i]] = fractions[i]
            sum_fraction = sum_fraction + fractions[i]
        assert sum_fraction.numerator <= sum_fraction.denominator
        self.c = len(self.constraint)
        self.labels = None

    def set_labels(self, labels):
        self.labels = labels
        assert len(self.labels) == len(self.constraint)

    def qualify(self, cd):
        assert self.labels is not None
        assert isinstance(cd, ColorDistribution)
        n = cd.sum()
        for i in range(cd.c):
            ni, pi = cd.d[i], self.constraint[self.labels[i]]
            if ni < n * pi.numerator / pi.denominator:
                return False
        return True


def load_representative_constraint(filename):
    with open(filename, "r") as fin:
        lines = list(fin.readlines())
        assert len(lines) == 3
        for i in range(3):
            lines[i] = lines[i].strip()

        column = lines[0]
        vals = [x for x in lines[1].split(",")]
        fractions = [
            Fraction(numerator=int(x.split("/")[0]), denominator=int(x.split("/")[1]))
            for x in lines[2].split(",")
        ]
        return column, RepresentativeConstraint(vals, fractions)
