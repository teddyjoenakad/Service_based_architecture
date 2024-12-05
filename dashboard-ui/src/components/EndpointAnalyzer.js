import React, { useEffect, useState } from 'react'
import '../App.css';

export default function EndpointAnalyzer(props) {
    const [isLoaded, setIsLoaded] = useState(false);
    const [log, setLog] = useState(null);
    const [error, setError] = useState(null)
	const rand_val = Math.floor(Math.random() * 100); // Get a random event from the event store
    const [index, setIndex] = useState(null);
    

    const getAnalyzer = () => {
        fetch(`http://kafka-group35.westus.cloudapp.azure.com/analyzer/${props.endpoint}?index=${rand_val}`)
            .then(res => res.json())
            .then((result)=>{
				console.log("Received Analyzer Results for " + props.endpoint)
                setLog(result);
                setIsLoaded(true);
                setIndex(rand_val);
            },(error) =>{
                setError(error)
                setIsLoaded(true);
            })
    }
	useEffect(() => {
		const interval = setInterval(() => getAnalyzer(), 4000); // Update every 4 seconds
		return() => clearInterval(interval);
    }, [getAnalyzer]);

    if (error){
        return (<div className={"error"}>Error found when fetching from API</div>)
    } else if (isLoaded === false){
        return(<div>Loading...</div>)
    } else if (isLoaded === true){
        
        return (
            <div>
                <h3>{props.endpoint}-{index}</h3>
                {JSON.stringify(log)}
            </div>
        )
    }
}
