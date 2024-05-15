import pandas as pd
from color_distribution import ColorDistribution


class Table:
    def __init__(
        self,
        representative_column=None,
        df=None,
        labels=None,
        filename=None,
        delimeter=",",
        index_col=None,
        dropna=True,
    ):
        self.representative_column = representative_column

        if filename is not None:
            self.df = pd.read_csv(filename, delimiter=delimeter, index_col=index_col)
            if dropna:
                self.df = self.df.dropna().reset_index(drop=True)
            # discretize the representative column into non-negative numbers
            self.missing_cnt = self.df.isnull().sum()
            self.df = self.df.astype(str)
            self.labels = None
            if self.representative_column:
                assert self.representative_column in self.df.columns
                self.df[self.representative_column], self.labels = pd.factorize(
                    self.df[self.representative_column]
                )
        elif df is not None:
            self.df = df
            self.labels = labels
        else:
            raise ValueError("Create a new table without data source")

        if self.representative_column:
            self._collect_color_distribution()

    def _collect_color_distribution(self):
        assert self.representative_column is not None
        _d = {}
        _df = self.df.groupby([self.representative_column]).size()
        for i in range(self.labels.shape[0]):
            _d[i] = 0
        # for idx, val in _df.iteritems():
        for idx, val in _df.items():
            _d[idx] += val
        self.color_distribution = ColorDistribution(self.labels.shape[0], _d)

    def nrows(self):
        return self.df.shape[0]

    def npairs(self):
        return self.nrows() * (self.nrows() - 1) // 2

    def ncols(self):
        return self.df.shape[1]

    def _get_subrows_by_filter(self, column_name, equal_to):
        return self.df[self.df[column_name] == equal_to]

    def get_subtable_by_filter(self, column_name, equal_to):
        return Table(
            self.representative_column,
            self._get_subrows_by_filter(column_name, equal_to).reset_index(drop=True),
            self.labels,
        )

    # return an empty table with the old header
    def get_empty_table(self):
        empty_df = self.df.iloc[0:0]
        return Table(self.representative_column, empty_df, self.labels)

    def get_distinct_vals_of(self, col):
        return self.df[col].unique().tolist()

    def get_representative_column_distribution(self):
        assert self.labels is not None and self.representative_column is not None
        self._collect_color_distribution()
        d = {}
        for color in range(self.color_distribution.c):
            d[self.labels[color]] = self.color_distribution.d[color]
        return d

    def __add__(self, other):
        _df = pd.concat([self.df, other.df], axis=0, ignore_index=True)
        return Table(self.representative_column, _df, self.labels)

    def __iadd__(self, other):
        self.df = pd.concat([self.df, other.df], axis=0, ignore_index=True)
        if self.representative_column is not None:
            self._collect_color_distribution()
        return self

    # a dataframe contains all the possible combination of (lhs1, lhs2)
    def group_by_two_lhs(self, lhs1, lhs2):
        return self.df[lhs1.cols + lhs2.cols].drop_duplicates(ignore_index=True)

    def get_subtable_by_query(self, query):
        _df = self.df.query(query).reset_index(drop=True)
        return Table(self.representative_column, _df, self.labels)

    def get_subtable_by_nums(self, nums):
        assert self.representative_column is not None
        res = self.get_empty_table()
        for k, v in nums.items():
            res = res + Table(
                self.representative_column,
                self.df.loc[self.df[self.representative_column] == k].head(v),
                self.labels,
            )
        return res

    def copy(self):
        return Table(self.representative_column, self.df.copy(), self.labels)

    def __repr__(self):
        _df = self.df.copy()
        if self.representative_column:
            for index in self.df.index:
                color = _df.at[index, self.representative_column]
                # color = _df.at[index, self.representative_column].item()
                _df.at[index, self.representative_column] = self.labels[color]
        return _df.to_string(index=False)

    def __str__(self):
        return self.__repr__()
