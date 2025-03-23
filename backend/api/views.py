from copy import deepcopy

from django.http import HttpResponse
from django.template import loader
from django.urls import reverse
from rest_framework import status, viewsets
from rest_framework.response import Response

from .reconciliation_engine import (
    REPORTS,
    generate_csv,
    generate_html,
    normalize_record,
    parse_csv,
    reconcile_data,
)
from .serializers import ReconciliationSerializer


def welcome(request):
    template = loader.get_template('welcome.html')
    return HttpResponse(template.render())


class ReconciliationViewSet(viewsets.ViewSet):
    def _build_url(self, report_id):
        relative_url = reverse('api:reconciliation-detail', kwargs={'pk': report_id})
        absolute_url = self.request.build_absolute_uri(relative_url)

        return absolute_url[:-1] + '?output=html'

    def list(self, request):
        """
        List reconciliation results that were previously computed.
        Given more time, we could store results in a proper DB like Postgres or Redis.
        For assement purposes, we'll use in-memory or SQLite.
        """
        reports = []
        payload = {'reports': reports, 'meta': {'total': 0}}

        if len(REPORTS.keys()) > 0:
            payload['meta']['total'] = len(REPORTS.keys())

            for report_id in REPORTS.keys():
                report = REPORTS[report_id]
                missing_in_target = len(report['missing_in_target'])
                missing_in_source = len(report['missing_in_source'])
                discrepancies = len(report['discrepancies'])

                reports.append(
                    {
                        'id': report_id,
                        'created_at': report['created_at'].strftime(
                            '%I:%M %p on %a, %-d %B, %Y'
                        ),
                        'outcome': f'{missing_in_target} missing in target, {missing_in_source} missing in source, {discrepancies} discrepancies',
                        'url': self._build_url(report_id),
                    }
                )

        return Response(payload, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None, format=None):
        """
        Download results that were previously computed. Given more time, we could store
        results in a proper DB like Postgres or Redis. For assement purposes, we'll use
        in-memory or SQLite.
        """
        output_format = self.request.query_params.get('output')

        report = REPORTS.get(pk)
        if not report:
            return Response(
                {'detail': 'Report not found.'}, status=status.HTTP_404_NOT_FOUND
            )

        results = deepcopy(report)
        results.pop('fields')
        results.pop('created_at')

        if output_format == 'csv':
            output = generate_csv(results)
            print(output)
            print(output.getvalue())
            response = HttpResponse(output.getvalue(), content_type='text/csv')
            response['Content-Disposition'] = (
                'attachment; filename="reconciliation.csv"'
            )

            return response

        elif output_format == 'html':
            html = generate_html({**results, 'id': pk})
            return HttpResponse(html, status=status.HTTP_200_OK)

        # default output_format is json
        return Response(
            {'id': pk, **results, 'report_url': self._build_url(pk)},
            status=status.HTTP_200_OK,
        )

    def create(self, request, format=None):
        """
        Accepts two CSV files, performs reconciliation, and returns the results
        in JSON, CSV, or HTML. The default format is JSON.
        """
        serializer = ReconciliationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        source_file = serializer.validated_data['source_file']
        target_file = serializer.validated_data['target_file']
        output_format = serializer.validated_data.get('output_format', 'json')

        print(type(source_file), type(target_file), type(output_format))
        print('source_file', source_file)
        print('target_file', target_file)
        print('output_format', output_format)

        # Parse CSVs
        source_raw = parse_csv(source_file)
        target_raw = parse_csv(target_file)

        print('source_raw', source_raw)
        print('target_raw', target_raw)

        # Normalize data
        source_data = [normalize_record(row) for row in source_raw]
        target_data = [normalize_record(row) for row in target_raw]

        print('source_data', source_data)
        print('target_data', target_data)

        # Reconcile
        report_id, fields, missing_in_target, missing_in_source, discrepancies = (
            reconcile_data(source_data, target_data)
        )

        print('missing_in_target', missing_in_target)
        print('missing_in_source', missing_in_source)
        print('discrepancies', discrepancies)

        # Prepare the results
        results = {
            'missing_in_target': missing_in_target,
            'missing_in_source': missing_in_source,
            'discrepancies': discrepancies,
        }

        if output_format == 'csv':
            output = generate_csv(results)
            response = HttpResponse(output.getvalue(), content_type='text/csv')
            response['Content-Disposition'] = (
                'attachment; filename="reconciliation.csv"'
            )

            return response

        elif output_format == 'html':
            html = generate_html({**results, 'fields': fields, 'id': report_id})
            return HttpResponse(html, status=status.HTTP_200_OK)

        # default format is json
        return Response(
            {'id': report_id, **results, 'report_url': self._build_url(report_id)},
            status=status.HTTP_200_OK,
        )
