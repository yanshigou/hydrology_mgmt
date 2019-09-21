// Call the dataTables jQuery plugin
$(document).ready(function () {
    $('#dataTable').DataTable({
        "language": {
            "decimal": "",
            "info": "显示 _START_ 条 至 _END_ 条 共 _TOTAL_ 条数据",
            "infoEmpty": "没有数据",
            "emptyTable": "没有数据",
            "infoFiltered": "(从总数 _MAX_ 条中 过滤)",
            "infoPostFix": "",
            "thousands": ",",
            "lengthMenu": "每页显示 _MENU_ 条数据",
            "loadingRecords": "加载中...",
            "processing": "处理中...",
            "search": "搜索:",
            "zeroRecords": "没有搜索到数据",
            "paginate": {
                "first": "第一页",
                "last": "最后一页",
                "next": "下一页",
                "previous": "上一页"
            },
            "aria": {
                "sortAscending": ": 点击以按升序排序",
                "sortDescending": ": 点击以按降序排序"
            }
        },
        // 'ordering': false,
        "order": [],
        // "columnDefs": [
        //     {"orderable": false, "targets": 0}
        // ]
    });
});
$(function () {
    $('#kaifazhong').click(function () {
        alert('开发中...')
    })
});
