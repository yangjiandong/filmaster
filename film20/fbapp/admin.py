from film20.fbapp.models import Contest, ContestTickets, ContestParticipation, Event
from django.contrib import admin
from django.utils.translation import ugettext as _
import datetime

class ContestParticipationAdmin(admin.ModelAdmin):
    list_display = ('user', 'contest', 'score', 'state')
    list_filter = ['contest', 'state']

class ContestTicketsInline(admin.TabularInline):
    model = ContestTickets
    raw_id_fields = ('theater',)

class ContestAdmin(admin.ModelAdmin):
    list_display = ('title', 'final_date', 'state')
    list_filter = ['state']
    exclude = ['tickets_old']

    inlines = [ContestTicketsInline]

    buttons = [{
        'name': 'copy',
        'short_description': _('Copy'),
    }]
    
    def change_view(self, request, object_id, extra_context={}):
        extra_context['buttons']=self.buttons
        if object_id is not None:
            import re
            res=re.match('(?P<id>\d+)/(?P<command>.*)', object_id)
            if res:
                if res.group('command') in [b['name'] for b in self.buttons]:
                    obj = self.model._default_manager.get(pk=res.group('id'))
                    ret = getattr(self, res.group('command'))(obj, request)
                    from django.http import HttpResponse, HttpResponseRedirect
                    if isinstance(ret, HttpResponse):
                        return ret
                    return HttpResponseRedirect(request.META['HTTP_REFERER'])
        return super(ContestAdmin, self).change_view(request, object_id, extra_context)

    def copy(self, obj, request):
        from django import http
        contest = obj.__class__.objects.create(
            title=obj.title,
            descr=obj.descr,
            state=obj.STATE_OPEN,
            final_date=obj.final_date + datetime.timedelta(days=7),
        )
        for t in obj.tickets.all():
            ContestTickets.objects.create(
                contest=contest,
                theater=t.theater,
                descr=t.descr,
                amount=t.amount)
        from django.contrib import messages
        messages.add_message(request, messages.INFO, _('Contest "%(obj)s" has been copied. You may edit it below.') % {'obj': unicode(contest)})
        return http.HttpResponseRedirect("../../%d/" % contest.id)

class ContestTicketsAdmin(admin.ModelAdmin):
    list_display = ('theater', 'descr', 'amount', )
    raw_id_fields = ('theater',)

class EventAdmin(ContestAdmin):
    list_display = ('title', 'slug', 'final_date', 'state' )

admin.site.register(ContestTickets, ContestTicketsAdmin)
admin.site.register(ContestParticipation, ContestParticipationAdmin)
admin.site.register(Contest, ContestAdmin)
admin.site.register(Event, EventAdmin)
