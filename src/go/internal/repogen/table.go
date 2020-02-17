package repogen

type Table struct {
	Name       string
	Package    string
	FilePrefix string
	Columns    []Column
}

type Column struct {
	Name    string
	Type    ColumnType
	Primary bool
	Indexes []string
	NotNull bool
}

func (t Table) PrimaryColumn() (Column, bool) {
	for _, c := range t.Columns {
		if c.Primary {
			return c, true
		}
	}
	return Column{}, false
}

func (t Table) Indexes() map[string][]Column {
	inds := make(map[string][]Column)
	for _, c := range t.Columns {
		for _, ind := range c.Indexes {
			if _, ok := inds[ind]; !ok {
				inds[ind] = nil
			}
			inds[ind] = append(inds[ind], c)
		}
	}
	return inds
}

type ColumnType string

const (
	String  ColumnType = "STRING"
	Int                = "INTEGER"
	Float64            = "FLOAT"
	Time               = "TIMESTAMP"
	Month              = "INTEGER"
	Weekday            = "INTEGER"
)

func (ct ColumnType) GoType() string {
	switch ct {
	case "STRING":
		return "string"
	case "INTEGER":
		return "int"
	case "FLOAT":
		return "float64"
	case "TIME":
		return "time.Time"
	case "MONTH":
		return "time.Month"
	case "WEEKDAY":
		return "time.Weekday"
	}
	panic("unknown column type")
}
