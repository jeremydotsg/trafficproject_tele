from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.views import View
from django.views import generic
from django.utils import timezone
from django.db.models import F, Max, OuterRef, Subquery
from .models import Queue, Direction, QueueStatus, QueueType, QueueLength
from .forms import QueueStatusForm
from django.utils.functional import empty
from datetime import timedelta
import datetime

#Create your views here.
class IndexView(View):
    def get(self,request):
        packed = {}
        direction_pack = {}
        #Get the number of directions
        for each_direction in Queue.objects.values_list('direction',flat=True).distinct():
            queue_pack = {}
            #Get the queues
            direction_name = Direction.objects.get(id=each_direction).directionName
            print('Direction:' + str(direction_name))
            for each_queue in Queue.objects.filter(direction=each_direction).all():
                print('Queue:' + str(each_queue))
                # Subquery to get the latest createdTime for each queue
                # Get the current time
                current_time = timezone.now()
                # Calculate the time one hour ago from the current time
                one_hour_ago = current_time - timedelta(days=365)
                latest_queue = QueueStatus.objects.filter(queue=each_queue,createdTime__gte=one_hour_ago).order_by('-createdTime')[:1]
                # Main query to get the latest queueLength for each queue
                if not latest_queue:
                    queue_pack[each_queue] = ''
                else:
                    for queue_status in latest_queue:
                        print('Status:' + str(queue_status))
                        queue_pack[each_queue] = queue_status
                direction_pack[direction_name] = queue_pack

        #print(direction_pack)
        data = {
            'packed': direction_pack
        }
        #print(data)
        return render(request, 'trafficdb/index.html', data)


def queue_list(request):
    queues = Queue.objects.all()
    queue_statuses = QueueStatus.objects.select_related('queue').all()
    context = {
        'queues': queues,
        'queue_statuses': queue_statuses
    }
    return render(request, 'trafficdb/queue_list.html', context)

def queue_detail(request, queue_id):
    queue = get_object_or_404(Queue, id=queue_id)
    queue_status = QueueStatus.objects.filter(queue=queue).order_by('-createdTime').first()
    if request.method == 'POST':
        form = QueueStatusForm(request.POST)
        if form.is_valid():
            new_status = form.save(commit=False)
            new_status.queue = queue
            new_status.save()
            return redirect('trafficdb:queue_detail', queue_id=queue.id)
    else:
        form = QueueStatusForm()
    context = {
        'queue': queue,
        'queue_status': queue_status,
        'form': form
    }
    return render(request, 'trafficdb/queue_detail.html', context)

def disclaimer(request):
    return render(request, 'trafficdb/disclaimer.html')
# class IndexView(generic.ListView):
#     template_name = "trafficdb/index.html"
#     context_object_name = "queueStatusList"
#
#     def get_queryset(self):
#         """
#         Return the last five published questions (not including those set to be
#         published in the future).
#         """
#         return QueueStatus.objects.filter(createdTime__lte=timezone.now()).order_by("-createdTime")[
#             :5
#         ]
