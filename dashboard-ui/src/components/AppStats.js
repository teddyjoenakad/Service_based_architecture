import React, { useEffect, useState } from 'react'
import '../App.css';

export default function AppStats() {
    const [isLoaded, setIsLoaded] = useState(false);
    const [stats, setStats] = useState({});
    const [error, setError] = useState(null)

	const getStats = () => {
	
        fetch(`http://acit3855-kafka2.westus.cloudapp.azure.com/processing`)
            .then(res => res.json())
            .then((result)=>{
				console.log("Received Stats")
                console.log(result)
                setStats(result);
                setIsLoaded(true);
            },(error) =>{
                setError(error)
                setIsLoaded(true);
            })
    }
    useEffect(() => {
		const interval = setInterval(() => getStats(), 2000); // Update every 2 seconds
		return() => clearInterval(interval);
    }, [getStats]);

    if (error){
        return (<div className={"error"}>Error found when fetching from API</div>)
    } else if (isLoaded === false){
        return(<div>Loading...</div>)
    } else if (isLoaded === true){
        return(
            <div>
                <h1>Latest Stats</h1>
                <table className={"StatsTable"}>
					<tbody>
						<tr>
							<th>Parking Status</th>
							<th>Payment</th>
						</tr>
						<tr>
							<td># Parking: {stats['total_status_events']}</td>
							<td># Payment: {stats['total_payment_events']}</td>
						</tr>
						<tr>
							<td colspan="2">Highest payment: {stats['highest_payment']}</td>
						</tr>
						<tr>
							<td colspan="2">Most frequent meter: {stats['most_frequent_meter']}</td>
						</tr>
					</tbody>
                </table>
                <h3>Last Updated: {stats['last_updated']}</h3>

            </div>
        )
    }
}
