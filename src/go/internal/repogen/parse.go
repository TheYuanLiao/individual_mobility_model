package repogen

import (
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"path/filepath"
	"reflect"
	"strconv"
	"strings"
)

func Parse(path, pkgName string) ([]Table, error) {
	fset := token.NewFileSet()
	pkgs, err := parser.ParseDir(fset, path, nil, 0)
	if err != nil {
		return nil, err
	}
	pkg := pkgs[pkgName]
	var tables []Table
	for fn, f := range pkg.Files {
		if strings.HasSuffix(fn, "_gen.go") {
			continue
		}
		filebase := strings.TrimSuffix(filepath.Base(fn), filepath.Ext(fn))
		var inspectErr error
		ast.Inspect(f, func(node ast.Node) bool {
			if t, ok := node.(*ast.TypeSpec); ok {
				if str, ok := t.Type.(*ast.StructType); ok {
					tbl := Table{
						Package:    pkgName,
						Name:       t.Name.Name,
						FilePrefix: filebase,
					}
					for _, f := range str.Fields.List {
						col := Column{
							Name: f.Names[0].Name,
						}
						typ, err := astType(f)
						if err != nil {
							inspectErr = err
							return false
						}
						col.Type = typ
						strTags(f, &col)
						tbl.Columns = append(tbl.Columns, col)
					}
					tables = append(tables, tbl)
				}
			}
			return true
		})
		if inspectErr != nil {
			return nil, inspectErr
		}
	}
	return tables, nil
}

func astType(field *ast.Field) (ColumnType, error) {
	if ident, ok := field.Type.(*ast.Ident); ok {
		switch ident.Name {
		case "int":
			return Int, nil
		case "string":
			return String, nil
		case "float64":
			return Float64, nil
		}
	}
	if sel, ok := field.Type.(*ast.SelectorExpr); ok {
		switch {
		case sel.Sel.Name == "Time" && sel.X.(*ast.Ident).Name == "time":
			return Time, nil
		case sel.Sel.Name == "Month" && sel.X.(*ast.Ident).Name == "time":
			return Month, nil
		case sel.Sel.Name == "Weekday" && sel.X.(*ast.Ident).Name == "time":
			return Weekday, nil
		}
	}
	return ColumnType("0"), fmt.Errorf("unknown column type: %s", field.Names[0].Name)
}

func strTags(field *ast.Field, c *Column) {
	if field.Tag == nil {
		return
	}
	unq, err := strconv.Unquote(field.Tag.Value)
	if err != nil {
		return
	}
	st := reflect.StructTag(unq)
	if _, ok := st.Lookup("pk"); ok {
		c.Primary = true
	}
	if _, ok := st.Lookup("notnull"); ok {
		c.NotNull = true
	}
	if idx, ok := st.Lookup("idx"); ok {
		idxs := strings.Split(idx, ",")
		for _, id := range idxs {
			c.Indexes = append(c.Indexes, id)
		}
	}
}
