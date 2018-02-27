# -*- coding: utf-8 -*-

import os
import re
from yandextank.core import AbstractPlugin
from jinja2 import Environment, FileSystemLoader, Template
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
import importlib


class MailPlugin(AbstractPlugin):

    SECTION = 'mail'
    STAGES = ['prepare_test', 'start_test',
              'end_test', 'post_process']
    EMAIL_ENCODING = 'utf-8'

    @staticmethod
    def get_key():
        return __file__

    def __init__(self, core):
        AbstractPlugin.__init__(self, core)
        self.sender = ''
        self.recievers = ''
        self.templates_dir_path = ''
        self.data_plugin = None
        self.stage_data = None
        self.templ_base_names = [
            'header_template', 'header_template_file_name',
            'message_template', 'message_template_file_name',
            'html_message_template', 'html_message_template_file_name']
        self.save_base_names = ['save_header_file',
                                'save_message_file',
                                'save_html_message_file']

    def get_available_options(self):
        options = ['templates_dir_path', 'from', 'to',
                   'data_plugin_module', 'data_plugin_class']
        base_names = self.templ_base_names
        for bn in self.save_base_names:
            base_names += ["%s_%s" % (bn, 'prefix'), "%s_%s" % (bn, 'suffix')]
        for bn in base_names:
            options += ["%s_%s" % (bn, stage)
                        for stage in MailPlugin.STAGES]
        return options

    def configure(self):
        self.sender = self.get_option('from', '')
        self.recievers = self.get_option('to', '')
        self.templates_dir_path = self.get_option('templates_dir_path', '')
        try:
            data_plugin_module = self.get_option('data_plugin_module')
            data_plugin_class = self.get_option('data_plugin_class')
            m = importlib.import_module(data_plugin_module)
            c = getattr(m, data_plugin_class)
            self.data_plugin = self.core.get_plugin_of_type(c)
        except Exception, exc:
            self.log.warning("No plugin providing data: %s" % exc)

    def start_test(self):
        self.send_mail('start_test')

    def end_test(self, retcode):
        self.send_mail('end_test')
        return retcode

    def prepare_test(self):
        self.send_mail('prepare_test')

    def post_process(self, retcode):
        self.send_mail('post_process')
        return retcode

    def render_template_value(self, base_name, stage):
        opt_name = "%s_%s" % (base_name, stage)
        template_value = self.get_option(opt_name, '')
        if not template_value:
            return ''

        t = Template(template_value)
        return t.render(self.stage_data)

    def render_template_message(self, base_name, stage):
        value = self.render_template_value(base_name, stage)
        if value:
            return value
        if not self.templates_dir_path:
            return ''

        opt_name = "%s_%s_%s" % (base_name, 'file_name', stage)
        file_name = self.get_option(opt_name,
                                    'mail_%s_%s' % (base_name, stage))
        file_path = os.path.join(self.templates_dir_path, file_name)
        if not os.path.exists(file_path):
            self.log.info("Template %s file is not exist." \
                          % file_path)
            return ''
        env = Environment(loader=FileSystemLoader(self.templates_dir_path))
        template = env.get_template(file_name)
        return template.render(self.stage_data)

    def send_mail(self, stage):
        if not self.data_plugin:
            self.log.warning("Stage: %s. Data plugin is not provided." % stage)
        self.stage_data = self.data_plugin.get_data(stage)
        try:
            report = self.render_template_message('message_template', stage)
            report_html = self.render_template_message('html_message_template',
                                                       stage)
            if not (report or report_html):
                self.log.info("Mail reports for %s stage are empty." % stage)
                return

            header_line = self.render_template_message('header_template',
                                                       stage)
            if header_line:
                self.log.info("Stage: %s. Mail subject: %s" % (stage,
                                                               header_line))
            else:
                self.log.warning("Stage: %s. Mail subject is empty." % stage)

            msg = MIMEMultipart('alternative')
            msg['Subject'] = Header(header_line, MailPlugin.EMAIL_ENCODING)
            msg['From'] = self.sender
            mail_list = re.split("[;, ]+", self.recievers)
            mail_list = [s for s in mail_list if s]
            msg['To'] = self.recievers

            part1 = MIMEText(report, 'text', MailPlugin.EMAIL_ENCODING)
            part2 = MIMEText(report_html, 'html', MailPlugin.EMAIL_ENCODING)
            msg.attach(part1)
            msg.attach(part2)
            s = smtplib.SMTP('localhost')
            s.sendmail(self.sender, mail_list, msg.as_string())
            self.log.info("Mail to %s was sent successfully" % mail_list)
            s.quit()
            self.save_messages(header_line, report, report_html, stage)
        except Exception, exc:
            self.log.warning("Exception on %s stage: %s" % (stage, exc))

    def save_messages(self, header, text, html, stage):
        content = {'header': header,
                   'message': text,
                   'html_message': html}
        for key in content:
            prefix_opt_name = "save_%s_file_prefix_%s" % (key, stage)
            suffix_opt_name = "save_%s_file_suffix_%s" % (key, stage)
            prefix = self.get_option(prefix_opt_name, '')
            if not prefix:
                continue
            suffix = self.get_option(suffix_opt_name, '')
            if not prefix:
                continue
            file_path = self.core.mkstemp(suffix, prefix)
            self.core.add_artifact_file(file_path)
            with open(file_path, 'w') as f:
                f.write(content[key])
