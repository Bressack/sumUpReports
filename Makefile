
all: build
	open -a "Google Chrome" ./reports

clean:
	rm -f ./reports/*.html

build:
	python3 sumup_report.py --csv sumup_report_20221109-1745_20221110-0030-afterwork.csv    --nb-client 120  --title "Afterwork 09/11/2022"
	python3 sumup_report.py --csv sumup_report_20221109-0000_20221109-1715-goodies.csv      --nb-client 70   --title "Goodies 09/11/2022"
	python3 sumup_report.py --csv 6-last_month_20220514-0000_20221113-2252-sales_report.csv --nb-client 1000 --title "last-six-months"
	python3 sumup_report.py --csv sumup_report_Halloween.csv                                --nb-client 705  --title "Halloween"

re: clean all
