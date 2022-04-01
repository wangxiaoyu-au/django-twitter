from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomizedPagination(PageNumberPagination):

    # default page size, when page is not set in the parameters of url
    page_size = 20
    # the client can set page size,
    # par exemple:
    # https://.../api/friendships/1/followers/?page=3&size=10
    page_size_query_param = 'size'
    # the max page size that the client can set
    max_page_size = 20

    # return to frontend
    def get_paginated_response(self, data):
        return Response({
            'total_results': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'page_number': self.page.number,
            'has_next_page': self.page.has_next(),
            'results': data,
        })

