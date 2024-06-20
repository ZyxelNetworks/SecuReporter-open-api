import gzip
import os
import re
import csv
import logging
from collections import defaultdict
import opensearchpy.helpers
from opensearchpy.connection import connections
from opensearchpy import Index, IndexTemplate, OpenSearch

from sr_es_template import *

logger = logging.getLogger(__name__)


class ReporterLogHelper():
    """
    A class for parsing and processing archive logs.
    """

    def __init__(self) -> None:
        self.batch_size = 10000
        self.opensearch_host = "localhost"

        self.archived_sr_log = os.path.join(os.path.abspath(os.getcwd()), "data", "2024-06-16.gzip")
        self.csv_export_path = os.path.join(os.path.abspath(os.getcwd()), "csv_results")

        self.category_mapping = {
            "0": {"name": "common", "es_doc": CommonInformation()},
            "1": {"name": "application_patrol", "es_doc": ApplicationPatrol()},
            "2": {"name": "traffic", "es_doc": Traffic()},
            "3": {"name": "anti_malware", "es_doc": AntiMalware()},
            "4": {"name": "threat_protection", "es_doc": ThreatProtection()},
            "5": {"name": "mail_protection", "es_doc": MailProtection()},
            "6": {"name": "web_protection", "es_doc": WebProtection()},
            "7": {"name": "ap_managed", "es_doc": APManaged()},
            "8": {"name": "dhcp_event", "es_doc": DHCPEvent()},
            "9": {"name": "system_service", "es_doc": SystemServiceStatus()},
            "10": {"name": "vpn_connection", "es_doc": VPNConnection()},
            "11": {"name": "interface_statistic", "es_doc": InterfaceStatistic()},
            "12": {"name": "user_event", "es_doc": UserLogin()},
            "13": {"name": "application_traffic", "es_doc": AppTraffic()},
            "14": {"name": "anti_botnet", "es_doc": AntiBotnet()},
            "15": {"name": "sandbox", "es_doc": Sandbox()},
            "16": {"name": "sandbox_statistics", "es_doc": SandboxStatistics()},
            "17": {"name": "device_event", "es_doc": DeviceEventType()},
            "18": {"name": "system_event", "es_doc": SystemEventType()},
            "19": {"name": "reputation", "es_doc": Reputation()},
            "20": {"name": "application_usage", "es_doc": AppPatrolUsageStatistics()},
            "21": {"name": "dns_filter", "es_doc": DNSFilter()},
            "22": {"name": "dns_content_filter", "es_doc": DNSContentFilter()},
            "23": {"name": "dut_scan_statistics", "es_doc": DUTScanStatistics()}
        }

        self.opensearch_connection = connections.create_connection(hosts=[self.opensearch_host])
        self.create_opensearch_tempate()

    def processing(self):
        """
        Process the archive logs and save the results to CSV files.
        """

        for file_batch_lines in self.open_archive_file(self.archived_sr_log):
            log_category = defaultdict(list)
            for file_line in file_batch_lines:
                dict_log = self.convert_archive_log_to_dict(file_line)

                log_category[self.category_mapping[str(
                    dict_log.pop('log_type'))].get('name')].append(dict_log)

            # export to OpenSearch
            for category, es_docs in log_category.items():
                self.import_log_to_opensearch(
                    idx_name=category, es_docs=es_docs)

            # export to csv file
            os.path.abspath(os.getcwd())

            os.makedirs(name=self.csv_export_path, exist_ok=True)
            for category, data_list in log_category.items():
                file_path = os.path.join(
                    self.csv_export_path, f"{str(category)}.csv")
                self.list_of_dict_to_csv(
                    data_list=data_list, filename=file_path)

    def open_archive_file(self, filename: str):
        """
        Opens an archive file and reads it line by line.
        """
        line_count = 0
        batch_read: list[str] = []
        with gzip.open(filename, 'rt', encoding='UTF-8') as zipfile:
            for line in zipfile:
                if line_count > self.batch_size:
                    yield batch_read
                    line_count = 0
                    batch_read.clear()
                batch_read.append(line)
                line_count += 1

    def convert_archive_log_to_dict(self, input_string_line: str) -> dict:
        """
        Converts a string line of archive log into a dictionary.

        Args:
            input_string_line (str): The input string line of archive log.

        Returns:
            dict: A dictionary containing the key-value pairs extracted from the input string line.

        """
        dict_log = {}
        pattern = re.compile(r'(\w+)="([^"]*)"')
        matches = pattern.findall(input_string_line)
        for k, v in matches:
            try:
                dict_log[k] = int(v)
            except ValueError:
                dict_log[k] = v
        if 'utc_time' in dict_log:
            dict_log['utc_time'] = int(dict_log['utc_time'] * 1000)

        return dict_log

    def list_of_dict_to_csv(self, data_list: list[dict], filename):
        """
        Writes a list of dictionaries to a CSV file.
        """
        is_file_exists = os.path.isfile(filename)
        if is_file_exists:
            append_write = 'a'
        else:
            append_write = 'w'

        with open(filename, append_write, newline='\n', encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=data_list[0].keys())
            if not is_file_exists:
                writer.writeheader()
            for row in data_list:
                writer.writerow(row)

    def create_opensearch_tempate(self):
        """
        Creates an OpenSearch index template for each log category.
        """
        for log_category in self.category_mapping.values():
            log_category_name = log_category.get('name')
            idx = Index(log_category_name)

            idx.document(log_category.get('es_doc'))
            it = IndexTemplate(name=log_category_name,
                               template=f"{log_category_name}*", index=idx)
            it.save()

    def import_log_to_opensearch(self, es_docs: list[dict], idx_name: str):
        """
        Imports documents from a CSV file to an OpenSearch index.
        """
        es_actions = []
        for doc in es_docs:
            es_doc = {
                '_index': idx_name,
                '_type': '_doc',
                '_source': doc}
            es_actions.append(es_doc)

        opensearchpy.helpers.bulk(client=OpenSearch(), actions=es_actions, max_retries=5,
                                  request_timeout=30)


if __name__ == '__main__':
    try:
        ReporterLogHelper().processing()
    except Exception as e:
        logger.exception("Error:")
