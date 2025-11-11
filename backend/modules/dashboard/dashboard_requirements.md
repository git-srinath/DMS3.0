

chart1: 
api - all_metrics
description - this api will fetch different metrics related to map references, jobs, active/inactive jobs etc.
            - this will fetch 6 metrics (count) 
required chart - use metirc cards to display each stat.  display all cards in single row at the top.



chart2:
api - jobs_overview
description - this api will fetch different information about jobs such as Map reference(job name), time processed, average rows processed, average target rows processed, max job duration, minimum job duration.
required chart - i want to display the data in the table view format. display table below the metric cards.



dropdown requirement - create a dropdown menu and list all the jobs which will be fetched from above api.



chart3:
api - jobs_processed_rows
description - this will fetch day(same day), week (last 7 days) and month (last 30 days) data of processed source and
            target rows for a particular map reference. need to send mapref and period as a paramaters.
            mapref is the job selected from the above dropdown. by default always use the first job of dropdown.
            
required chart - use a good and suitable chart. provide option to select period. 


chart4:
api - jobs_processed_rows
description - this will fetch day(same day), week (last 7 days) and month (last 30 days) data of execution time in seconds
             for a particular map reference. need to send mapref and period as a paramaters.
            mapref is the job selected from the above dropdown. by default always use the first job of dropdown.
            
required chart - use a good and suitable chart. provide option to select period. 




chart5:
api - jobs_average_run_duration
description - this will fetch the average run duration for all jobs. output contains job name and avarge run duration in seconds. no filter option required. this is for all jobs.
required chart -    use a good and suitable chart.


chart6:
api - jobs_successful_failed
description - this will fetch count of how many times job is filed and ran sucessfully for all jobs. no filter is requird.
required chart -    use a good and suitable chart.




Dashboard requirements:
1. use chart.js
2. use best of the best deisgn and styling for creating charts and dashboard.
3. should be modern looking and visually stunning dashboard.
4. use complate page width.
5. should be responsive.

if there are any issues with backend code please fix.
in the frontend,for each chart, create a separate chrt component and kee it in the same folder(dashboard).
let me know if you need any clarity before implemnting this dashboard.

