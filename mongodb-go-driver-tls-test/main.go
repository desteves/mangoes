package main

import (
	"fmt"

	"github.com/mongodb/mongo-go-driver/mongo"
	"github.com/mongodb/mongo-go-driver/mongo/options"
)

func main() {
	testTLS()
	testTLSWithKey()

}

func testTLS() {
	cs := "mongodb://localhost:8989"
	pf := "/Users/d/go/src/github.com/desteves/mongo-go-ssl-test/mongod.pem"
	ca := "/Users/d/go/src/github.com/desteves/mongo-go-ssl-test/ca.pem"
	opts := options.Client().
		SetAppName("chaos-agent").
		SetSingle(true).
		SetSSL(&options.SSLOpt{
			Enabled:                  true,
			ClientCertificateKeyFile: pf,
			Insecure:                 false,
			CaFile:                   ca,
		})
	_, err := mongo.NewClientWithOptions(cs, opts)
	if err != nil {
		fmt.Println("testTLS", err)
	} else {
		fmt.Println("testTLS works!")
	}
}

func testTLSWithKey() {
	cs := "mongodb://localhost:8989"
	pp := "qwerty"
	pf := "/Users/d/go/src/github.com/desteves/mongo-go-ssl-test/mongod_pass_qwerty.pem"
	ca := "/Users/d/go/src/github.com/desteves/mongo-go-ssl-test/ca.pem"

	f := func() string {
		return pp
	}

	opts := options.Client().
		SetAppName("chaos-agent").
		SetSingle(true).
		SetSSL(&options.SSLOpt{
			Enabled:                      true,
			ClientCertificateKeyFile:     pf,
			ClientCertificateKeyPassword: f,
			Insecure:                     false,
			CaFile:                       ca,
		})
	_, err := mongo.NewClientWithOptions(cs, opts)
	if err != nil {
		fmt.Println("testTLSWithKey", err)
	} else {
		fmt.Println("testTLSWithKey works!")
	}

}
